# Inference Server Development Plan

**App**: Inference Server (Stable Diffusion + LoRA)  
**Last Updated**: 2025-11-05  
**Status**: M1 In Progress

---

## Overview

This document contains detailed subtasks for inference server development. For high-level milestones, see [root PLAN.md](../../PLAN.md).

**Reference Documents**:
- [Inference Server README.md](README.md) - Architecture and deployment
- [Inference Server CODE_GUIDE.md](CODE_GUIDE.md) - Code patterns
- [API Documentation](../../docs/API.md) - Webhook specifications

---

## M1: Foundation

### M1-Initialization

**Referenced by**: Root PLAN.md → PT-M1-Inference  
**Status**: PLANNED

#### Subtasks

- [x] Install Stable Diffusion dependencies
  - [x] Create requirements.txt with diffusers, transformers
  - [x] Install pillow for image processing
  - [x] Verify CUDA availability

- [x] RabbitMQ connection test
  - [x] Install pika library
  - [x] Test connection to RabbitMQ
  - [x] Declare image_generation queue

- [x] Test inference with base model
  - [x] Load Stable Diffusion v1.5
  - [x] Generate test image with default prompt
  - [x] Verify image quality

**Exit Criteria**:
- [ ] Stable Diffusion loads without errors
- [ ] CUDA is available
- [ ] Can generate test image

---

## M4: AI Integration

### M4-Inference-Pipeline

**Referenced by**: Root PLAN.md → PT-M4-Inference  
**Status**: PLANNED

#### Subtasks

- [ ] Stable Diffusion inference
  - [ ] Load base model (Stable Diffusion v1.5)
  - [ ] Configure inference (50 steps, guidance_scale=7.5)
  - [ ] Support aspect ratios (1:1, 16:9, 9:16, 4:3, 3:4)
  - [ ] Handle seed for reproducibility

- [ ] LoRA weight loading
  - [ ] Load LoRA weights from file path
  - [ ] Apply LoRA to base model
  - [ ] Verify style is applied to generated image

- [ ] Signature insertion with PIL
  - [ ] Load signature image
  - [ ] Resize signature based on size parameter (small, medium, large)
  - [ ] Composite signature onto generated image
  - [ ] Support positions: bottom-left, bottom-center, bottom-right
  - [ ] Apply opacity (0.0 - 1.0)

- [ ] Batch processing
  - [ ] Support up to 10 concurrent generations
  - [ ] Queue management for requests
  - [ ] Resource allocation per generation

- [ ] RabbitMQ Consumer
  - [ ] Create consumer for image_generation queue
  - [ ] Parse message (generation_id, style_id, lora_path, prompt, aspect_ratio, seed, webhook_url)
  - [ ] Call generation function
  - [ ] Send status updates to webhook

- [ ] Status update via PATCH /api/images/:id/status
  - [ ] Send status=processing when started
  - [ ] Send status=completed with image_url when done
  - [ ] Send status=failed with failure_reason on error

**Implementation Reference**: [CODE_GUIDE.md#inference-pipeline](CODE_GUIDE.md#inference-pipeline)

**Exit Criteria**:
- [ ] Can generate image with LoRA in < 10 seconds
- [ ] Signature inserted correctly
- [ ] Status updates sent to backend

---

### M4-Signature-Validation

**Referenced by**: Root PLAN.md → CP-M4-2  
**Status**: PLANNED

#### Subtasks

- [ ] Position accuracy test
  - [ ] Test bottom-left, bottom-center, bottom-right positions
  - [ ] Verify signature within 5px tolerance

- [ ] Opacity range test
  - [ ] Test opacity values 0.0, 0.5, 1.0
  - [ ] Verify visual appearance

- [ ] Size scaling test
  - [ ] Test small, medium, large sizes
  - [ ] Verify signature scales correctly

- [ ] Metadata embedding
  - [ ] Embed artist_id and model_id in image EXIF
  - [ ] Verify metadata persists after save

- [ ] Visual inspection
  - [ ] Generate 10 sample images
  - [ ] Manually verify signature quality

**Exit Criteria**:
- [ ] Signature appears in correct position
- [ ] Opacity and size work as expected
- [ ] Metadata embedded correctly

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
python generate_image.py --generation_id 1

# Testing
pytest

# Monitoring
nvidia-smi
```

---

**Note**: This plan is a living document. Update it as you complete tasks and encounter new requirements.
