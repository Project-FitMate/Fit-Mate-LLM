import base64
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.config import settings


@dataclass
class GeneratedImage:
    data: bytes
    mime_type: str


def _client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


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
