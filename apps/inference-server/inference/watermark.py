"""Watermark and signature insertion for generated images."""

import logging
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)


class WatermarkService:
    """
    Service for inserting artist signatures and watermarks into generated images.

    Supports different positions, sizes, and opacity levels.
    """

    # Position presets
    POSITIONS = {
        "bottom-left": lambda img_size, wm_size: (10, img_size[1] - wm_size[1] - 10),
        "bottom-center": lambda img_size, wm_size: (
            (img_size[0] - wm_size[0]) // 2,
            img_size[1] - wm_size[1] - 10,
        ),
        "bottom-right": lambda img_size, wm_size: (
            img_size[0] - wm_size[0] - 10,
            img_size[1] - wm_size[1] - 10,
        ),
        "top-left": lambda img_size, wm_size: (10, 10),
        "top-center": lambda img_size, wm_size: ((img_size[0] - wm_size[0]) // 2, 10),
        "top-right": lambda img_size, wm_size: (img_size[0] - wm_size[0] - 10, 10),
    }

    # Size presets (as percentage of image width)
    SIZES = {
        "small": 0.15,
        "medium": 0.25,
        "large": 0.35,
    }

    def __init__(self):
        """Initialize watermark service."""
        logger.info("WatermarkService initialized")

    def insert_signature(
        self,
        image: Image.Image,
        signature_image: Image.Image,
        position: str = "bottom-right",
        size: str = "medium",
        opacity: float = 0.7,
    ) -> Image.Image:
        """
        Insert artist signature image as watermark.

        Args:
            image: Original PIL Image
            signature_image: Signature image (PNG with transparency)
            position: Position preset (default: "bottom-right")
            size: Size preset (default: "medium")
            opacity: Opacity 0.0-1.0 (default: 0.7)

        Returns:
            PIL Image with signature inserted

        Raises:
            ValueError: If position or size is invalid
        """
        logger.info(f"Inserting signature: position={position}, size={size}, opacity={opacity}")

        if position not in self.POSITIONS:
            raise ValueError(f"Invalid position: {position}. Valid: {list(self.POSITIONS.keys())}")

        if size not in self.SIZES:
            raise ValueError(f"Invalid size: {size}. Valid: {list(self.SIZES.keys())}")

        if not (0.0 <= opacity <= 1.0):
            raise ValueError(f"Opacity must be between 0.0 and 1.0, got {opacity}")

        # Copy image to avoid modifying original
        result = image.copy()

        # Convert to RGBA for transparency
        if result.mode != "RGBA":
            result = result.convert("RGBA")

        # Calculate signature size
        signature_width = int(result.width * self.SIZES[size])
        aspect_ratio = signature_image.height / signature_image.width
        signature_height = int(signature_width * aspect_ratio)

        # Resize signature
        signature_resized = signature_image.resize(
            (signature_width, signature_height), Image.Resampling.LANCZOS
        )

        # Convert signature to RGBA
        if signature_resized.mode != "RGBA":
            signature_resized = signature_resized.convert("RGBA")

        # Apply opacity
        signature_with_opacity = self._apply_opacity(signature_resized, opacity)

        # Calculate position
        pos_x, pos_y = self.POSITIONS[position](result.size, signature_with_opacity.size)

        # Paste signature
        result.paste(signature_with_opacity, (pos_x, pos_y), signature_with_opacity)

        # Convert back to RGB
        result = result.convert("RGB")

        logger.info(f"Signature inserted at ({pos_x}, {pos_y})")
        return result

    def insert_text_watermark(
        self,
        image: Image.Image,
        text: str,
        position: str = "bottom-right",
        font_size: int = 20,
        opacity: float = 0.7,
        color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        Insert text watermark.

        Args:
            image: Original PIL Image
            text: Watermark text
            position: Position preset (default: "bottom-right")
            font_size: Font size in pixels (default: 20)
            opacity: Opacity 0.0-1.0 (default: 0.7)
            color: RGB color tuple (default: white)

        Returns:
            PIL Image with text watermark
        """
        logger.info(f"Inserting text watermark: '{text}' at {position}")

        # Copy image
        result = image.copy()

        # Convert to RGBA
        if result.mode != "RGBA":
            result = result.convert("RGBA")

        # Create transparent overlay
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to load font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            logger.warning("Font not found, using default font")
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position
        wm_size = (text_width, text_height)
        pos_x, pos_y = self.POSITIONS[position](result.size, wm_size)

        # Apply opacity to color
        alpha = int(255 * opacity)
        color_with_alpha = (*color, alpha)

        # Draw text
        draw.text((pos_x, pos_y), text, font=font, fill=color_with_alpha)

        # Composite
        result = Image.alpha_composite(result, overlay)

        # Convert back to RGB
        result = result.convert("RGB")

        logger.info(f"Text watermark inserted")
        return result

    def _apply_opacity(self, image: Image.Image, opacity: float) -> Image.Image:
        """
        Apply opacity to image.

        Args:
            image: RGBA PIL Image
            opacity: Opacity 0.0-1.0

        Returns:
            Image with adjusted opacity
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Get alpha channel
        alpha = image.split()[3]

        # Multiply alpha by opacity
        alpha = alpha.point(lambda p: int(p * opacity))

        # Replace alpha channel
        image.putalpha(alpha)

        return image

    def add_metadata(
        self,
        image: Image.Image,
        metadata: dict,
    ) -> Image.Image:
        """
        Add metadata to image (EXIF/PNG info).

        Args:
            image: PIL Image
            metadata: Dictionary of metadata

        Returns:
            Image with metadata
        """
        logger.info(f"Adding metadata: {metadata}")

        # For PNG images, use info dict
        if image.format == "PNG" or not hasattr(image, "format"):
            from PIL import PngImagePlugin

            meta = PngImagePlugin.PngInfo()
            for key, value in metadata.items():
                meta.add_text(str(key), str(value))

            # Save and reload to apply metadata
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", pnginfo=meta)
            buffer.seek(0)
            return Image.open(buffer)

        # For JPEG, use EXIF
        # (Implementation would go here if needed)

        return image


def insert_artist_signature(
    image: Image.Image,
    signature_path: str,
    position: str = "bottom-right",
    size: str = "medium",
    opacity: float = 0.7,
) -> Image.Image:
    """
    Convenience function to insert artist signature.

    Args:
        image: Original image
        signature_path: Path to signature image file
        position: Position preset
        size: Size preset
        opacity: Opacity level

    Returns:
        Image with signature

    Raises:
        FileNotFoundError: If signature file not found
    """
    import os

    if not os.path.exists(signature_path):
        raise FileNotFoundError(f"Signature image not found: {signature_path}")

    signature_image = Image.open(signature_path)

    service = WatermarkService()
    return service.insert_signature(image, signature_image, position, size, opacity)
