from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


class TranslationError(RuntimeError):
    pass


class Translator(Protocol):
    name: str

    def translate(self, text: str) -> str: ...


@dataclass(slots=True)
class TranslateShellTranslator:
    executable: str = "trans"
    name: str = "translate-shell"

    def translate(self, text: str) -> str:
        process = subprocess.run(
            [self.executable, "-brief", ":en", text],
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        if process.returncode != 0:
            raise TranslationError(process.stderr.strip() or "translate-shell failed")
        translated = process.stdout.strip()
        if not translated:
            raise TranslationError("translate-shell returned an empty result")
        return translated


@dataclass(slots=True)
class DeepTranslator:
    name: str = "deep-translator"

    def translate(self, text: str) -> str:
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise TranslationError("deep-translator is not installed") from exc
        result = GoogleTranslator(source="auto", target="en").translate(text)
        if not result:
            raise TranslationError("deep-translator returned an empty result")
        return result


@dataclass(slots=True)
class LibreTranslateTranslator:
    endpoint: str
    api_key: str | None = None
    name: str = "libretranslate"

    def translate(self, text: str) -> str:
        payload = {"q": text, "source": "auto", "target": "en", "format": "text"}
        if self.api_key:
            payload["api_key"] = self.api_key
        request = urllib.request.Request(
            self.endpoint.rstrip("/") + "/translate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # network error details vary by platform
            raise TranslationError(f"LibreTranslate request failed: {exc}") from exc
        result = body.get("translatedText")
        if not result:
            raise TranslationError(f"Unexpected LibreTranslate response: {body}")
        return str(result)


def select_translator(preferred: str = "auto") -> Translator:
    preferred = preferred.lower()
    if preferred in {"auto", "trans", "translate-shell"} and shutil.which("trans"):
        return TranslateShellTranslator(shutil.which("trans") or "trans")
    if preferred in {"auto", "deep", "deep-translator"}:
        try:
            import deep_translator  # noqa: F401
            return DeepTranslator()
        except ImportError:
            if preferred != "auto":
                raise TranslationError("Install with: pip install 'magic-sorter-x[translate]'")
    endpoint = os.getenv("LIBRETRANSLATE_URL")
    if preferred in {"auto", "libre", "libretranslate"} and endpoint:
        return LibreTranslateTranslator(endpoint, os.getenv("LIBRETRANSLATE_API_KEY"))
    raise TranslationError(
        "No translation backend found. Install Translate Shell (`trans`), install the "
        "translate extra, or set LIBRETRANSLATE_URL."
    )


def _should_translate(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and not stripped.startswith(("http://", "https://"))


def translate_text(text: str, translator: Translator, max_chars: int = 3500) -> str:
    """Translate text in backend-friendly chunks while preserving paragraph breaks."""
    if len(text) <= max_chars:
        return translator.translate(text)

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for paragraph in text.split("\n"):
        addition = len(paragraph) + (1 if current else 0)
        if current and current_length + addition > max_chars:
            chunks.append("\n".join(current))
            current = []
            current_length = 0
        if len(paragraph) > max_chars:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_length = 0
            chunks.extend(paragraph[i:i + max_chars] for i in range(0, len(paragraph), max_chars))
        else:
            current.append(paragraph)
            current_length += addition
    if current:
        chunks.append("\n".join(current))
    return "\n".join(translator.translate(chunk) for chunk in chunks if chunk)


def translate_value(
    value: Any,
    translator: Translator,
    translate_keys: bool = False,
    _cache: dict[str, str] | None = None,
) -> Any:
    cache = {} if _cache is None else _cache

    def translated(text: str) -> str:
        if not _should_translate(text):
            return text
        if text not in cache:
            cache[text] = translate_text(text, translator)
        return cache[text]

    if isinstance(value, str):
        return translated(value)
    if isinstance(value, list):
        return [translate_value(item, translator, translate_keys, cache) for item in value]
    if isinstance(value, dict):
        output: dict[Any, Any] = {}
        for key, child in value.items():
            new_key = translated(key) if translate_keys and isinstance(key, str) else key
            output[new_key] = translate_value(child, translator, translate_keys, cache)
        return output
    return value


def translate_xml_value(
    value: Any,
    translator: Translator,
    _cache: dict[str, str] | None = None,
) -> Any:
    """Translate XML text nodes while preserving element names and attributes."""
    cache = {} if _cache is None else _cache

    if isinstance(value, str):
        if not _should_translate(value):
            return value
        if value not in cache:
            cache[value] = translate_text(value, translator)
        return cache[value]
    if isinstance(value, list):
        return [translate_xml_value(item, translator, cache) for item in value]
    if isinstance(value, dict):
        output: dict[Any, Any] = {}
        for key, child in value.items():
            if key == "@attributes":
                output[key] = child
            else:
                output[key] = translate_xml_value(child, translator, cache)
        return output
    return value
