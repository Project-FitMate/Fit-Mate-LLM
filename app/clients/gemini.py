import base64
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.config import settings


@dataclass
class GeneratedImage:
    data: bytes
    mime_type: str


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


def _image_part(data_b64: str, mime_type: str) -> types.Part:
    return types.Part.from_bytes(data=base64.b64decode(data_b64), mime_type=mime_type)


def generate_text(system_prompt: str, user_prompt: str, images: list[tuple[str, str]] | None = None) -> str:
    """Generate text. images is list of (base64, mime_type)."""
    parts: list[types.Part | str] = [user_prompt]
    if images:
        parts.extend(_image_part(b64, mt) for b64, mt in images)

    response = _client().models.generate_content(
        model=settings.gemini_text_model,
        contents=parts,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return (response.text or "").strip()


def compose_images(system_prompt: str, user_prompt: str, images: list[tuple[str, str]]) -> GeneratedImage:
    """Compose multiple images via Gemini image model. Returns first image part."""
    parts: list[types.Part | str] = [user_prompt]
    parts.extend(_image_part(b64, mt) for b64, mt in images)

    response = _client().models.generate_content(
        model=settings.gemini_image_model,
        contents=parts,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )

    for candidate in response.candidates or []:
        for part in candidate.content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                return GeneratedImage(data=inline.data, mime_type=inline.mime_type or "image/png")

    raise RuntimeError("Gemini did not return an image")
