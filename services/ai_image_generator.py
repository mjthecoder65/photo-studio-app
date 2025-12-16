import io
from typing import BinaryIO

import google.generativeai as genai
from opentelemetry import trace
from PIL import Image

from configs.settings import settings

# Get tracer for this module
tracer = trace.get_tracer(__name__)


class AIImageGeneratorService:
    """Service for AI-powered image generation using Gemini API."""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_IMAGE_MODEL)

    async def generate_image_from_text(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        response_modalities: list[str] = None,
    ) -> tuple[bytes, str]:

        with tracer.start_as_current_span(
            "generate_image_from_text",
            attributes={
                "ai.model": settings.GEMINI_IMAGE_MODEL,
                "ai.prompt_length": len(prompt),
                "ai.aspect_ratio": aspect_ratio,
            },
        ) as span:
            try:
                if response_modalities is None:
                    response_modalities = ["IMAGE"]

                generation_config = {
                    "response_modalities": response_modalities,
                }
                if aspect_ratio:
                    generation_config["image_config"] = {
                        "aspect_ratio": aspect_ratio,
                    }

                # Add sub-span for API call
                with tracer.start_as_current_span("gemini_api_call"):
                    response = self.model.generate_content(
                        prompt,
                        generation_config=generation_config,
                    )

                for part in response.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = part.inline_data.data
                        mime_type = part.inline_data.mime_type or "image/png"

                        # Add attributes to span
                        span.set_attribute("ai.image_size_bytes", len(image_data))
                        span.set_attribute("ai.mime_type", mime_type)
                        span.set_attribute("ai.success", True)

                        return image_data, mime_type

                raise Exception("No image generated in response")

            except Exception as e:
                span.set_attribute("ai.success", False)
                span.set_attribute("ai.error", str(e))
                span.record_exception(e)
                raise Exception(f"Failed to generate image: {str(e)}")

    async def generate_image_from_text_and_image(
        self,
        prompt: str,
        reference_image: BinaryIO,
        aspect_ratio: str = "1:1",
    ) -> tuple[bytes, str]:
        """
        Generate an image from text prompt and reference image.

        Args:
            prompt: Text description for image modification
            reference_image: Reference image file
            reference_mime_type: MIME type of reference image
            aspect_ratio: Aspect ratio for the generated image

        Returns:
            tuple: (image_bytes, content_type)

        Raises:
            Exception: If image generation fails
        """
        with tracer.start_as_current_span(
            "generate_image_from_text_and_image",
            attributes={
                "ai.model": settings.GEMINI_IMAGE_MODEL,
                "ai.prompt_length": len(prompt),
                "ai.aspect_ratio": aspect_ratio,
                "ai.has_reference_image": True,
            },
        ) as span:
            try:
                reference_image.seek(0)
                image_bytes = reference_image.read()
                img = Image.open(io.BytesIO(image_bytes))

                # Add reference image size to span
                span.set_attribute("ai.reference_image_size_bytes", len(image_bytes))

                generation_config = {
                    "response_modalities": ["IMAGE"],
                    "image_config": {
                        "aspect_ratio": aspect_ratio,
                    },
                }

                # Add sub-span for API call
                with tracer.start_as_current_span("gemini_api_call_with_image"):
                    response = self.model.generate_content(
                        [img, prompt],
                        generation_config=generation_config,
                    )

                for part in response.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = part.inline_data.data
                        mime_type = part.inline_data.mime_type or "image/png"

                        # Add attributes to span
                        span.set_attribute("ai.image_size_bytes", len(image_data))
                        span.set_attribute("ai.mime_type", mime_type)
                        span.set_attribute("ai.success", True)

                        return image_data, mime_type

                raise Exception("No image generated in response")

            except Exception as e:
                span.set_attribute("ai.success", False)
                span.set_attribute("ai.error", str(e))
                span.record_exception(e)
                raise Exception(f"Failed to generate image from reference: {str(e)}")

    def get_supported_aspect_ratios(self) -> list[str]:
        """
        Get list of supported aspect ratios.

        Returns:
            list: Supported aspect ratios
        """

        return [
            "1:1",  # Square (1024x1024)
            "2:3",  # Portrait (832x1248)
            "3:2",  # Landscape (1248x832)
            "3:4",  # Portrait (864x1184)
            "4:3",  # Landscape (1184x864)
            "4:5",  # Portrait (896x1152)
            "5:4",  # Landscape (1152x896)
            "9:16",  # Vertical (768x1344)
            "16:9",  # Horizontal (1344x768)
            "21:9",  # Ultra-wide (1536x672)
        ]
