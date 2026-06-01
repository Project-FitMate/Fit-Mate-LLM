import base64
import io
from dataclasses import dataclass

from google import genai
from google.genai import types
from PIL import Image

from app.config import settings


@dataclass
class GeneratedImage:
    data: bytes
    mime_type: str


def _to_jpeg(data: bytes) -> bytes:
    """Normalize any decodable image (GIF/WebP/PNG/HEIC-as-bytes/etc.) to RGB JPEG.

    Naver shop images are served with a .jpg extension but are sometimes GIF or
    other formats Gemini's image model rejects. Re-encoding to JPEG guarantees a
    format Gemini accepts for both query generation and image fusion.
    """
    with Image.open(io.BytesIO(data)) as img:
        rgb = img.convert("RGB")
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=90)
        return buf.getvalue()


_CLIENT: genai.Client | None = None


def _client() -> genai.Client:
    # Cache the client at module scope. google-genai's sync Client owns an
    # httpx.Client that gets closed when the Client is garbage-collected; a
    # fresh Client per call can be collected mid-request and surface as
    # "Cannot send a request, as the client has been closed."
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = genai.Client(api_key=settings.gemini_api_key)
    return _CLIENT


def _image_part(data_b64: str) -> types.Part:
    # Always re-encode to JPEG so Gemini receives a supported format regardless
    # of the source format (Naver images may be GIF/WebP despite a .jpg URL).
    jpeg = _to_jpeg(base64.b64decode(data_b64))
    return types.Part.from_bytes(data=jpeg, mime_type="image/jpeg")


def generate_text(system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
    """Generate text. images is a list of base64-encoded image strings."""
    parts: list[types.Part | str] = [user_prompt]
    if images:
        parts.extend(_image_part(b64) for b64 in images)

    response = _client().models.generate_content(
        model=settings.gemini_text_model,
        contents=parts,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return (response.text or "").strip()


def compose_images(system_prompt: str, user_prompt: str, images: list[str]) -> GeneratedImage:
    """Compose multiple images via Gemini image model. Returns first image part.

    images is a list of base64-encoded image strings.
    """
    parts: list[types.Part | str] = [user_prompt]
    parts.extend(_image_part(b64) for b64 in images)

    response = _client().models.generate_content(
        model=settings.gemini_image_model,
        contents=parts,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )

    text_chunks: list[str] = []
    finish_reasons: list[str] = []
    for candidate in response.candidates or []:
        finish_reasons.append(str(getattr(candidate, "finish_reason", None)))
        for part in candidate.content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                return GeneratedImage(data=inline.data, mime_type=inline.mime_type or "image/png")
            txt = getattr(part, "text", None)
            if txt:
                text_chunks.append(txt)

    prompt_feedback = getattr(response, "prompt_feedback", None)
    print(
        f"[fitting] image_model={settings.gemini_image_model} "
        f"finish_reasons={finish_reasons} "
        f"prompt_feedback={prompt_feedback!r} "
        f"text={' '.join(text_chunks)[:500]!r}",
        flush=True,
    )
    raise RuntimeError("Gemini did not return an image")
