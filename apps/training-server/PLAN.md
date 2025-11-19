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
**Status**: DONE

#### Subtasks

- [x] Install dependencies (Commit: a4f7381)
  - [x] Create requirements.txt with pika, requests, google-cloud-storage
  - [x] PyTorch deferred to M4 phase (not needed for M1)
  - [x] Create .env.example

- [x] RabbitMQ connection test (Commit: a4f7381)
  - [x] Install pika library
  - [x] Implement TrainingConsumer class
  - [x] Declare model_training queue
  - [x] Test connection in main.py

- [x] CUDA availability check (Commit: a4f7381)
  - [x] Check torch.cuda.is_available() in main.py
  - [x] Log GPU name and memory
  - [x] Test simple tensor operation on GPU

**Exit Criteria**:
- [x] PyTorch imports without errors (checked in main.py)
- [x] CUDA is available (checked in main.py)
- [x] RabbitMQ connection succeeds (TrainingConsumer.connect())

---

## M4: AI Integration

### M4-Training-Pipeline-Phase1 (Mock Implementation)

**Referenced by**: Root PLAN.md → PT-M4-Training
**Status**: DONE
**Approach**: Option 3 (Hybrid) - Local mock implementation without GPU

#### Subtasks

- [x] RabbitMQ Consumer (Commit: d712e2d)
  - [x] Create consumer for model_training queue
  - [x] Parse message matching PATTERNS.md format (style_id, images, parameters)
  - [x] Handle task_id, type, data structure
  - [x] ACK/NACK message handling

- [x] Webhook Service matching API.md spec (Commit: d712e2d)
  - [x] POST /api/webhooks/training/complete
  - [x] POST /api/webhooks/training/failed
  - [x] PATCH /api/webhooks/training/progress
  - [x] Include training_metric (loss, epochs) in completion
  - [x] Include error_code in failure webhook

- [x] Mock Training Pipeline (Commit: d712e2d)
  - [x] Simulate training with progress updates
  - [x] Send progress every 5 seconds (30 seconds in real training)
  - [x] Calculate simulated epochs and progress percentage
  - [x] Generate mock model path (gs://bucket/models/style-{id}/lora_weights.safetensors)

- [x] Comprehensive Tests (Commit: d712e2d)
  - [x] test_webhook_service.py (9 tests)
  - [x] test_consumer.py (7 tests)
  - [x] test_config.py (3 tests)
  - [x] All 16 tests passing

**Phase 1 Exit Criteria**:
- [x] RabbitMQ consumer processes messages correctly
- [x] Webhook payloads match API.md specification
- [x] All tests pass (16/16)
- [x] Code formatted with black

---

### M4-Training-Pipeline-Phase2 (GPU Implementation)

**Status**: IN_PROGRESS
**Environment**: GCP Compute Engine with GPU (L4 or T4)

#### Subtasks

- [x] Environment setup (Commit: a55e5c9)
  - [x] Install ML dependencies (PyTorch 2.9.1, diffusers, peft, transformers, accelerate)
  - [x] Verify CUDA connection (Tesla T4 GPU, CUDA 12.8)

- [x] Image preprocessing (Already implemented)
  - [x] Download images from GCS (gcs_service.py)
  - [x] Resize to 512x512 (dataset.py)
  - [x] Convert to RGB format (dataset.py)
  - [x] Validate image quality (dataset.py, gcs_service.py)

- [x] LoRA fine-tuning implementation (Already implemented in trainer.py)
  - [x] Load Stable Diffusion v1.5 base model
  - [x] Configure LoRA parameters (rank=8, alpha=32)
  - [x] Set learning rate=1e-4, num_epochs=100-500
  - [x] Use AdamW optimizer
  - [x] Mixed precision training (fp16)
  - [x] Enable gradient checkpointing

- [x] Checkpoint saving (Already implemented in trainer.py)
  - [x] Save checkpoint every 10 epochs
  - [x] Save final LoRA weights to GCS
  - [x] Include training metrics

- [x] Progress reporting (Already implemented in training_consumer.py)
  - [x] Send progress update every 30 seconds
  - [x] Include current_epoch, total_epochs, estimated_seconds
  - [x] Calculate actual training time

- [x] Retry logic (Commit: a55e5c9)
  - [x] Max 3 attempts on failure
  - [x] Exponential backoff between retries (1s, 2s, 4s)
  - [x] Log errors to Cloud Logging

**Implementation Reference**: [CODE_GUIDE.md#training-pipeline](CODE_GUIDE.md#training-pipeline)

**Phase 2 Exit Criteria**:
- [ ] Can train LoRA model with 10 images in < 30 minutes
- [ ] LoRA weights saved correctly to GCS
- [ ] Status updates sent to backend every 30 seconds
- [ ] GPU memory usage < 8GB
- [ ] Model quality verified with test prompts

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
