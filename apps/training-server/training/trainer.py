"""LoRA Fine-tuning trainer for Stable Diffusion models."""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import torch
from diffusers import StableDiffusionPipeline, DDPMScheduler, AutoencoderKL, UNet2DConditionModel
from peft import LoraConfig, get_peft_model
from accelerate import Accelerator
from transformers import CLIPTextModel, CLIPTokenizer
from torch.utils.data import DataLoader

from training.dataset import StyleImageDataset

logger = logging.getLogger(__name__)


class LoRATrainer:
    """
    LoRA Fine-tuning trainer for style models.

    Uses Stable Diffusion v1.5 as base model and PEFT LoRA for efficient fine-tuning.
    Supports mixed precision training (FP16) and progress reporting via callbacks.
    """

    def __init__(
        self,
        style_id: int,
        output_dir: str,
        model_name: str = "stable-diffusion-v1-5/stable-diffusion-v1-5",
        lora_rank: int = 8,
        lora_alpha: int = 32,
        learning_rate: float = 1e-4,
        num_epochs: int = 100,
        batch_size: int = 1,
        gradient_accumulation_steps: int = 4,
        mixed_precision: str = "fp16",
        enable_checkpointing: bool = True,
        checkpoint_every: int = 10,
    ):
        """
        Initialize LoRA trainer.

        Args:
            style_id: Style model ID
            output_dir: Directory to save trained model
            model_name: Base model name (default: SD v1.5)
            lora_rank: LoRA rank (default: 8)
            lora_alpha: LoRA alpha (default: 32)
            learning_rate: Learning rate (default: 1e-4)
            num_epochs: Number of training epochs (default: 100)
            batch_size: Batch size (default: 1)
            gradient_accumulation_steps: Gradient accumulation steps (default: 4)
            mixed_precision: Mixed precision mode (default: "fp16")
            enable_checkpointing: Enable gradient checkpointing (default: True)
            checkpoint_every: Save checkpoint every N epochs (default: 10)
        """
        self.style_id = style_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model_name = model_name
        self.lora_rank = lora_rank
        self.lora_alpha = lora_alpha
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.mixed_precision = mixed_precision
        self.enable_checkpointing = enable_checkpointing
        self.checkpoint_every = checkpoint_every

        # Initialize accelerator
        self.accelerator = Accelerator(
            mixed_precision=mixed_precision,
            gradient_accumulation_steps=gradient_accumulation_steps,
        )

        logger.info(f"LoRATrainer initialized for style {style_id}")
        logger.info(f"  Output: {output_dir}")
        logger.info(f"  LoRA rank={lora_rank}, alpha={lora_alpha}")
        logger.info(f"  Learning rate={learning_rate}, epochs={num_epochs}")

    def _load_models(self):
        """Load Stable Diffusion models (UNet, VAE, Text Encoder)."""
        logger.info(f"Loading base model: {self.model_name}")

        # Load pipeline
        pipeline = StableDiffusionPipeline.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.mixed_precision == "fp16" else torch.float32,
        )

        # Extract components
        self.vae = pipeline.vae
        self.text_encoder = pipeline.text_encoder
        self.tokenizer = pipeline.tokenizer
        self.unet = pipeline.unet
        self.scheduler = DDPMScheduler.from_config(pipeline.scheduler.config)

        # Freeze VAE and text encoder
        self.vae.requires_grad_(False)
        self.text_encoder.requires_grad_(False)

        # Move VAE to device
        self.vae = self.vae.to(self.accelerator.device)
        self.text_encoder = self.text_encoder.to(self.accelerator.device)

        logger.info("Base models loaded successfully")

    def _setup_lora(self):
        """Setup LoRA for UNet."""
        logger.info("Setting up LoRA...")

        # LoRA configuration
        lora_config = LoraConfig(
            r=self.lora_rank,
            lora_alpha=self.lora_alpha,
            target_modules=["to_q", "to_k", "to_v", "to_out.0"],
            lora_dropout=0.1,
            bias="none"
        )

        # Apply LoRA to UNet
        self.unet = get_peft_model(self.unet, lora_config)
        self.unet.train()

        # Enable gradient checkpointing for memory efficiency
        if self.enable_checkpointing:
            self.unet.enable_gradient_checkpointing()

        logger.info(f"LoRA applied to UNet (trainable params: {self.unet.num_parameters(only_trainable=True):,})")

    def _create_dataloader(self, image_paths: list[str]) -> DataLoader:
        """
        Create dataloader for training images.

        Args:
            image_paths: List of image file paths

        Returns:
            DataLoader instance
        """
        dataset = StyleImageDataset(
            image_paths=image_paths,
            target_size=512,
            normalize=True
        )

        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=True
        )

        logger.info(f"DataLoader created: {len(dataset)} images, batch_size={self.batch_size}")
        return dataloader

    def train(
        self,
        image_paths: list[str],
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        progress_interval: int = 30,
    ) -> str:
        """
        Execute LoRA fine-tuning.

        Args:
            image_paths: List of training image paths
            progress_callback: Callback function(current_epoch, total_epochs, loss)
                              Called every `progress_interval` seconds
            progress_interval: Progress callback interval in seconds (default: 30)

        Returns:
            Path to saved LoRA weights

        Raises:
            RuntimeError: If training fails
        """
        try:
            logger.info(f"Starting training for style {self.style_id}")
            logger.info(f"  Images: {len(image_paths)}")
            logger.info(f"  Epochs: {self.num_epochs}")

            # Load models
            self._load_models()
            self._setup_lora()

            # Create dataloader
            dataloader = self._create_dataloader(image_paths)

            # Optimizer
            optimizer = torch.optim.AdamW(
                self.unet.parameters(),
                lr=self.learning_rate,
                betas=(0.9, 0.999),
                weight_decay=0.01,
                eps=1e-8
            )

            # Prepare with accelerator
            self.unet, optimizer, dataloader = self.accelerator.prepare(
                self.unet, optimizer, dataloader
            )

            # Training loop
            global_step = 0
            last_callback_time = time.time()
            total_loss = 0.0

            for epoch in range(self.num_epochs):
                epoch_loss = 0.0

                for step, (images, _) in enumerate(dataloader):
                    with self.accelerator.accumulate(self.unet):
                        # Encode images to latent space
                        latents = self.vae.encode(images).latent_dist.sample()
                        latents = latents * 0.18215  # Scaling factor

                        # Sample noise
                        noise = torch.randn_like(latents)

                        # Sample timesteps
                        batch_size = latents.shape[0]
                        timesteps = torch.randint(
                            0, self.scheduler.config.num_train_timesteps,
                            (batch_size,),
                            device=latents.device
                        ).long()

                        # Add noise to latents
                        noisy_latents = self.scheduler.add_noise(latents, noise, timesteps)

                        # Get text embeddings (empty prompt for unconditional training)
                        text_input = self.tokenizer(
                            [""] * batch_size,
                            padding="max_length",
                            max_length=self.tokenizer.model_max_length,
                            truncation=True,
                            return_tensors="pt"
                        )
                        text_embeddings = self.text_encoder(text_input.input_ids.to(self.accelerator.device))[0]

                        # Predict noise
                        noise_pred = self.unet(noisy_latents, timesteps, text_embeddings).sample

                        # Calculate loss
                        loss = torch.nn.functional.mse_loss(noise_pred, noise, reduction="mean")

                        # Backward pass
                        self.accelerator.backward(loss)
                        optimizer.step()
                        optimizer.zero_grad()

                        # Track loss
                        epoch_loss += loss.detach().item()
                        global_step += 1

                # Calculate average epoch loss
                avg_epoch_loss = epoch_loss / len(dataloader)
                total_loss += avg_epoch_loss

                logger.info(f"Epoch {epoch + 1}/{self.num_epochs} - Loss: {avg_epoch_loss:.4f}")

                # Save checkpoint
                if (epoch + 1) % self.checkpoint_every == 0:
                    checkpoint_path = self.output_dir / f"checkpoint-epoch-{epoch + 1}"
                    self._save_checkpoint(checkpoint_path, epoch + 1)

                # Progress callback
                current_time = time.time()
                if progress_callback and (current_time - last_callback_time >= progress_interval):
                    progress_callback(epoch + 1, self.num_epochs, avg_epoch_loss)
                    last_callback_time = current_time

            # Save final model
            final_path = self.output_dir / "lora_weights"
            self._save_checkpoint(final_path, self.num_epochs, is_final=True)

            logger.info(f"Training completed successfully")
            logger.info(f"  Average loss: {total_loss / self.num_epochs:.4f}")
            logger.info(f"  Model saved to: {final_path}")

            return str(final_path)

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise RuntimeError(f"LoRA training failed for style {self.style_id}") from e

    def _save_checkpoint(self, save_path: Path, epoch: int, is_final: bool = False):
        """
        Save model checkpoint.

        Args:
            save_path: Path to save checkpoint
            epoch: Current epoch number
            is_final: Whether this is the final checkpoint
        """
        save_path.mkdir(parents=True, exist_ok=True)

        # Unwrap model from accelerator
        unwrapped_unet = self.accelerator.unwrap_model(self.unet)

        # Save LoRA weights
        unwrapped_unet.save_pretrained(save_path)

        # Save metadata
        metadata = {
            "style_id": self.style_id,
            "epoch": epoch,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "learning_rate": self.learning_rate,
            "is_final": is_final
        }

        import json
        with open(save_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Checkpoint saved: {save_path} (epoch {epoch})")


def train_lora_model(
    style_id: int,
    train_image_paths: list[str],
    output_dir: str,
    num_epochs: int = 100,
    learning_rate: float = 1e-4,
    progress_callback: Optional[Callable] = None
) -> str:
    """
    Convenience function to train a LoRA model.

    Args:
        style_id: Style model ID
        train_image_paths: List of training image paths
        output_dir: Directory to save trained model
        num_epochs: Number of training epochs (default: 100)
        learning_rate: Learning rate (default: 1e-4)
        progress_callback: Progress callback function

    Returns:
        Path to saved LoRA weights
    """
    trainer = LoRATrainer(
        style_id=style_id,
        output_dir=output_dir,
        num_epochs=num_epochs,
        learning_rate=learning_rate
    )

    return trainer.train(
        image_paths=train_image_paths,
        progress_callback=progress_callback
    )
