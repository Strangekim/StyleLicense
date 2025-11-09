# Training Server Development Plan

**App**: Training Server (PyTorch + LoRA)  
**Last Updated**: 2025-11-05  
**Status**: M1 In Progress

---

## Overview

This document contains detailed subtasks for training server development. For high-level milestones, see [root PLAN.md](../../PLAN.md).

**Reference Documents**:
- [Training Server README.md](README.md) - Architecture and deployment
- [Training Server CODE_GUIDE.md](CODE_GUIDE.md) - Code patterns
- [API Documentation](../../docs/API.md) - Webhook specifications

---

## M1: Foundation

### M1-Initialization

**Referenced by**: Root PLAN.md → PT-M1-Training
**Status**: PLANNED

#### Subtasks

- [ ] Install PyTorch and Diffusers
  - [ ] Create requirements.txt with torch, diffusers, transformers, peft
  - [ ] Install accelerate for distributed training
  - [ ] Verify CUDA availability

- [ ] RabbitMQ connection test
  - [ ] Install pika library
  - [ ] Test connection to RabbitMQ
  - [ ] Declare model_training queue

- [ ] CUDA availability check
  - [ ] Check torch.cuda.is_available()
  - [ ] Log GPU name and memory
  - [ ] Test simple tensor operation on GPU

**Exit Criteria**:
- [ ] PyTorch imports without errors
- [ ] CUDA is available
- [ ] RabbitMQ connection succeeds

---

## M4: AI Integration

### M4-Training-Pipeline

**Referenced by**: Root PLAN.md → PT-M4-Training  
**Status**: PLANNED

#### Subtasks

- [ ] Image preprocessing
  - [ ] Download images from S3 or URL
  - [ ] Resize to 512x512
  - [ ] Convert to RGB format
  - [ ] Validate image quality

- [ ] LoRA fine-tuning implementation
  - [ ] Load Stable Diffusion v1.5 base model
  - [ ] Configure LoRA parameters (rank=4, alpha=32)
  - [ ] Set learning rate=1e-4, num_epochs=100-500
  - [ ] Use AdamW optimizer
  - [ ] Mixed precision training (fp16)

- [ ] Checkpoint saving
  - [ ] Save checkpoint every 10 epochs
  - [ ] Save final LoRA weights to /models/{model_id}/lora_weights.safetensors
  - [ ] Upload to S3 if configured

- [ ] RabbitMQ Consumer
  - [ ] Create consumer for model_training queue
  - [ ] Parse message (style_id, image_paths, webhook_url, num_epochs)
  - [ ] Call training function
  - [ ] Send status updates to webhook

- [ ] Status update via PATCH /api/models/:id/status
  - [ ] Send training_status=processing when started
  - [ ] Send training_status=completed with model_path when done
  - [ ] Send training_status=failed with failure_reason on error

- [ ] Retry logic
  - [ ] Max 3 attempts on failure
  - [ ] Exponential backoff between retries
  - [ ] Log errors to file

**Implementation Reference**: [CODE_GUIDE.md#training-pipeline](CODE_GUIDE.md#training-pipeline)

**Exit Criteria**:
- [ ] Can train LoRA model with 10 images in < 30 minutes
- [ ] LoRA weights saved correctly
- [ ] Status updates sent to backend

---

## Quick Reference

### Task Status Tracking

When completing subtasks:
1. Mark subtask with [x] in this file
2. Update corresponding task in root PLAN.md when all subtasks done
3. Run tests to verify completion

### Common Commands

```bash
# Development
python rabbitmq_consumer.py
python train_lora.py --style_id 1

# Testing
pytest

# Monitoring
nvidia-smi
```

---

**Note**: This plan is a living document. Update it as you complete tasks and encounter new requirements.
