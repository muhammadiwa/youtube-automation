"""Thumbnail optimization and processing.

Handles thumbnail image optimization and dimension compliance.
Requirements: 15.3, 15.4, 15.5
"""

import io
import uuid
from typing import Optional, Tuple

from PIL import Image

# YouTube thumbnail specifications
YOUTUBE_THUMBNAIL_WIDTH = 1280
YOUTUBE_THUMBNAIL_HEIGHT = 720
YOUTUBE_THUMBNAIL_ASPECT_RATIO = 16 / 9
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB


class ThumbnailOptimizationError(Exception):
    """Base exception for thumbnail optimization errors."""
    pass


class ThumbnailOptimizer:
    """Handles thumbnail image optimization."""

    def __init__(
        self,
        target_width: int = YOUTUBE_THUMBNAIL_WIDTH,
        target_height: int = YOUTUBE_THUMBNAIL_HEIGHT,
    ):
        """Initialize optimizer.

        Args:
            target_width: Target width in pixels
            target_height: Target height in pixels
        """
        self.target_width = target_width
        self.target_height = target_height

    def optimize(
        self,
        image_data: bytes,
        enhance_quality: bool = True,
        apply_branding: bool = False,
        brand_logo_data: Optional[bytes] = None,
    ) -> Tuple[bytes, dict]:
        """Optimize thumbnail image.

        Args:
            image_data: Raw image data
            enhance_quality: Whether to enhance image quality
            apply_branding: Whether to apply branding
            brand_logo_data: Optional brand logo image data

        Returns:
            Tuple[bytes, dict]: Optimized image data and metadata

        Raises:
            ThumbnailOptimizationError: If optimization fails
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            original_width, original_height = image.size
            original_format = image.format or "JPEG"

            optimizations_applied = []

            # Convert to RGB if necessary (for JPEG output)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
                optimizations_applied.append("converted_to_rgb")

            # Resize to target dimensions
            if image.size != (self.target_width, self.target_height):
                image = self._resize_and_crop(image)
                optimizations_applied.append("resized")

            # Enhance quality if requested
            if enhance_quality:
                image = self._enhance_image(image)
                optimizations_applied.append("enhanced")

            # Apply branding if requested
            if apply_branding and brand_logo_data:
                image = self._apply_branding(image, brand_logo_data)
                optimizations_applied.append("branding_applied")

            # Save optimized image
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=95, optimize=True)
            optimized_data = output.getvalue()

            # Compress if file size exceeds limit
            if len(optimized_data) > MAX_FILE_SIZE_BYTES:
                optimized_data = self._compress_to_size(image, MAX_FILE_SIZE_BYTES)
                optimizations_applied.append("compressed")

            metadata = {
                "original_dimensions": {"width": original_width, "height": original_height},
                "final_dimensions": {"width": self.target_width, "height": self.target_height},
                "file_size_bytes": len(optimized_data),
                "optimizations_applied": optimizations_applied,
            }

            return optimized_data, metadata

        except Exception as e:
            raise ThumbnailOptimizationError(f"Optimization failed: {str(e)}") from e

    def _resize_and_crop(self, image: Image.Image) -> Image.Image:
        """Resize and crop image to target dimensions.

        Args:
            image: PIL Image

        Returns:
            Image.Image: Resized and cropped image
        """
        # Calculate aspect ratios
        target_ratio = self.target_width / self.target_height
        image_ratio = image.width / image.height

        if image_ratio > target_ratio:
            # Image is wider - crop width
            new_height = self.target_height
            new_width = int(new_height * image_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Center crop
            left = (new_width - self.target_width) // 2
            image = image.crop((left, 0, left + self.target_width, self.target_height))
        else:
            # Image is taller - crop height
            new_width = self.target_width
            new_height = int(new_width / image_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Center crop
            top = (new_height - self.target_height) // 2
            image = image.crop((0, top, self.target_width, top + self.target_height))

        return image

    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Apply image enhancements.

        Args:
            image: PIL Image

        Returns:
            Image.Image: Enhanced image
        """
        from PIL import ImageEnhance

        # Slightly increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)

        # Slightly increase color saturation
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)

        # Slightly increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)

        return image

    def _apply_branding(
        self,
        image: Image.Image,
        logo_data: bytes,
    ) -> Image.Image:
        """Apply brand logo to image.

        Args:
            image: PIL Image
            logo_data: Logo image data

        Returns:
            Image.Image: Image with branding
        """
        logo = Image.open(io.BytesIO(logo_data))

        # Resize logo to fit in corner (max 15% of thumbnail width)
        max_logo_width = int(self.target_width * 0.15)
        if logo.width > max_logo_width:
            ratio = max_logo_width / logo.width
            logo = logo.resize(
                (max_logo_width, int(logo.height * ratio)),
                Image.Resampling.LANCZOS,
            )

        # Convert logo to RGBA if needed
        if logo.mode != "RGBA":
            logo = logo.convert("RGBA")

        # Position in bottom-right corner with padding
        padding = 20
        position = (
            self.target_width - logo.width - padding,
            self.target_height - logo.height - padding,
        )

        # Paste logo with transparency
        image.paste(logo, position, logo)

        return image

    def _compress_to_size(
        self,
        image: Image.Image,
        max_size: int,
    ) -> bytes:
        """Compress image to fit within size limit.

        Args:
            image: PIL Image
            max_size: Maximum file size in bytes

        Returns:
            bytes: Compressed image data
        """
        quality = 95
        while quality > 10:
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)
            data = output.getvalue()
            if len(data) <= max_size:
                return data
            quality -= 5

        # If still too large, return at minimum quality
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=10, optimize=True)
        return output.getvalue()

    def validate_dimensions(self, image_data: bytes) -> Tuple[bool, dict]:
        """Validate image dimensions.

        Args:
            image_data: Raw image data

        Returns:
            Tuple[bool, dict]: (is_valid, dimensions)
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size

            is_valid = (width == self.target_width and height == self.target_height)

            return is_valid, {"width": width, "height": height}

        except Exception as e:
            raise ThumbnailOptimizationError(f"Validation failed: {str(e)}") from e


def optimize_thumbnail(
    image_data: bytes,
    target_width: int = YOUTUBE_THUMBNAIL_WIDTH,
    target_height: int = YOUTUBE_THUMBNAIL_HEIGHT,
    enhance_quality: bool = True,
) -> Tuple[bytes, dict]:
    """Convenience function to optimize a thumbnail.

    Args:
        image_data: Raw image data
        target_width: Target width
        target_height: Target height
        enhance_quality: Whether to enhance quality

    Returns:
        Tuple[bytes, dict]: Optimized image data and metadata
    """
    optimizer = ThumbnailOptimizer(target_width, target_height)
    return optimizer.optimize(image_data, enhance_quality=enhance_quality)
