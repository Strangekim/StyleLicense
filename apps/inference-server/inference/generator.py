"""Image generation using Stable Diffusion with LoRA weights."""

import os
import logging
from typing import Optional, Callable, Tuple
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Image generator using Stable Diffusion with LoRA weights.

    Supports different aspect ratios and provides progress callbacks.
    """

    # Aspect ratio to resolution mapping
    ASPECT_RATIOS = {
        "1:1": (512, 512),
        "2:2": (1024, 1024),
        "1:2": (512, 1024),
        "2:1": (1024, 512),
    }

    def __init__(
        self,
        model_name: str = "stable-diffusion-v1-5/stable-diffusion-v1-5",
        device: str = "cuda",
        torch_dtype = torch.float16,
    ):
        """
        Initialize image generator.

        Args:
            model_name: Base model name (default: SD v1.5)
            device: Device to use (default: "cuda")
            torch_dtype: Torch data type (default: float16)
        """
        self.model_name = model_name
        self.device = device
        self.torch_dtype = torch_dtype
        self.pipeline = None

        logger.info(f"ImageGenerator initialized")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Device: {device}")
        logger.info(f"  Dtype: {torch_dtype}")

    def _load_pipeline(self, lora_weights_path: Optional[str] = None):
        """
        Load Stable Diffusion pipeline.

        Args:
            lora_weights_path: Path to LoRA weights (optional)
        """
        if self.pipeline is not None:
            logger.info("Pipeline already loaded, skipping")
            return

        logger.info(f"Loading Stable Diffusion pipeline: {self.model_name}")

        # Load base model
        self.pipeline = StableDiffusionPipeline.from_pretrained(
            self.model_name,
            torch_dtype=self.torch_dtype,
        )

        # Move to device
        self.pipeline = self.pipeline.to(self.device)

        # Optimize scheduler for faster inference
        self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipeline.scheduler.config
        )

        # Enable memory optimizations
        if hasattr(self.pipeline, 'enable_attention_slicing'):
            self.pipeline.enable_attention_slicing()

        if hasattr(self.pipeline, 'enable_vae_slicing'):
            self.pipeline.enable_vae_slicing()

        logger.info("Pipeline loaded successfully")

        # Load LoRA weights if provided
        if lora_weights_path:
            self._load_lora_weights(lora_weights_path)

    def _load_lora_weights(self, lora_weights_path: str):
        """
        Load LoRA weights into pipeline.

        Args:
            lora_weights_path: Path to LoRA weights directory or file

        Raises:
            FileNotFoundError: If LoRA weights not found
        """
        if not os.path.exists(lora_weights_path):
            raise FileNotFoundError(f"LoRA weights not found: {lora_weights_path}")

        logger.info(f"Loading LoRA weights from: {lora_weights_path}")

        # Load LoRA weights
        self.pipeline.load_lora_weights(lora_weights_path)

        logger.info("LoRA weights loaded successfully")

    def get_resolution(self, aspect_ratio: str) -> Tuple[int, int]:
        """
        Get resolution for aspect ratio.

        Args:
            aspect_ratio: Aspect ratio string (e.g., "1:1", "2:2", "1:2")

        Returns:
            Tuple of (width, height)

        Raises:
            ValueError: If aspect ratio is not supported
        """
        if aspect_ratio not in self.ASPECT_RATIOS:
            raise ValueError(
                f"Unsupported aspect ratio: {aspect_ratio}. "
                f"Supported: {list(self.ASPECT_RATIOS.keys())}"
            )

        return self.ASPECT_RATIOS[aspect_ratio]

    def generate(
        self,
        prompt: str,
        lora_weights_path: Optional[str] = None,
        aspect_ratio: str = "1:1",
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Image.Image:
        """
        Generate image from prompt.

        Args:
            prompt: Text prompt for generation
            lora_weights_path: Path to LoRA weights (optional)
            aspect_ratio: Aspect ratio (default: "1:1")
            num_inference_steps: Number of inference steps (default: 50)
            guidance_scale: Guidance scale (default: 7.5)
            seed: Random seed for reproducibility (optional)
            progress_callback: Progress callback function(current_step, total_steps)

        Returns:
            Generated PIL Image

        Raises:
            RuntimeError: If generation fails
        """
        try:
            logger.info(f"Starting image generation")
            logger.info(f"  Prompt: {prompt}")
            logger.info(f"  LoRA weights: {lora_weights_path or 'None'}")
            logger.info(f"  Aspect ratio: {aspect_ratio}")
            logger.info(f"  Steps: {num_inference_steps}")

            # Load pipeline
            self._load_pipeline(lora_weights_path)

            # Get resolution
            width, height = self.get_resolution(aspect_ratio)
            logger.info(f"  Resolution: {width}x{height}")

            # Setup generator for reproducibility
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
                logger.info(f"  Seed: {seed}")

            # Define callback wrapper for progress reporting
            def callback_wrapper(step: int, timestep: int, latents: torch.Tensor):
                if progress_callback:
                    progress_callback(step, num_inference_steps)

            # Generate image
            result = self.pipeline(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                callback=callback_wrapper,
                callback_steps=1,
            )

            image = result.images[0]

            logger.info("Image generated successfully")
            logger.info(f"  Size: {image.size}")

            return image

        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate image") from e

    def unload_pipeline(self):
        """Unload pipeline to free memory."""
        if self.pipeline:
            del self.pipeline
            self.pipeline = None
            torch.cuda.empty_cache()
            logger.info("Pipeline unloaded")


def generate_image(
    prompt: str,
    lora_weights_path: Optional[str] = None,
    aspect_ratio: str = "1:1",
    num_inference_steps: int = 50,
    seed: Optional[int] = None,
    progress_callback: Optional[Callable] = None,
) -> Image.Image:
    """
    Convenience function to generate an image.

    Args:
        prompt: Text prompt
        lora_weights_path: Path to LoRA weights (optional)
        aspect_ratio: Aspect ratio (default: "1:1")
        num_inference_steps: Number of inference steps (default: 50)
        seed: Random seed (optional)
        progress_callback: Progress callback function

    Returns:
        Generated PIL Image
    """
    generator = ImageGenerator()

    try:
        image = generator.generate(
            prompt=prompt,
            lora_weights_path=lora_weights_path,
            aspect_ratio=aspect_ratio,
            num_inference_steps=num_inference_steps,
            seed=seed,
            progress_callback=progress_callback,
        )
        return image
    finally:
        generator.unload_pipeline()
