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
**Status**: DONE

#### Subtasks

- [x] Install Stable Diffusion dependencies (Commit: 617d7a5)
  - [x] Create requirements.txt with dependencies (pika, requests, pillow)
  - [x] Install pillow for image processing
  - [x] Note: ML dependencies (torch, diffusers) deferred to M4 for GPU instance

- [x] RabbitMQ connection test (Commit: 617d7a5)
  - [x] Install pika library
  - [x] Create config.py for environment management
  - [x] Create RabbitMQ consumer for image_generation queue
  - [x] Declare image_generation queue

- [x] Mock inference pipeline (Commit: 617d7a5)
  - [x] Create mock generation with progress updates (10 seconds simulation)
  - [x] Webhook integration for status updates
  - [x] Tests written and passing (5/5 tests)

**Exit Criteria**:
- [x] RabbitMQ consumer created and tested
- [x] Mock generation pipeline functional
- [x] Webhook service integrated
- [x] All tests passing (5/5)

---

## M4: AI Integration

### M4-Inference-Pipeline

**Referenced by**: Root PLAN.md → PT-M4-Inference
**Status**: IN_PROGRESS (Phase 1 DONE, Phase 2 PLANNED)

**Development Approach**: Following Option 3 (Hybrid) like training-server
- Phase 1: Mock implementation locally (DONE)
- Phase 2: GPU implementation on GCP (PLANNED)

---

#### Phase 1: Mock Implementation (DONE)

**Status**: DONE
**Commit**: eb2d393

##### Subtasks

- [x] RabbitMQ Consumer for `image_generation` queue (Commit: 617d7a5)
  - [x] Connect to RabbitMQ with proper credentials
  - [x] Declare `image_generation` queue
  - [x] Parse message format (generation_id, style_id, prompt, etc.)
  - [x] Process generation task with mock pipeline

- [x] Webhook service matching API.md spec (Commit: eb2d393)
  - [x] PATCH /api/webhooks/inference/progress with progress object
  - [x] POST /api/webhooks/inference/complete with result_url and metadata
  - [x] POST /api/webhooks/inference/failed with error_message and error_code
  - [x] Authentication with INTERNAL_API_TOKEN header
  - [x] X-Request-Source: inference-server header

- [x] Mock generation pipeline (Commit: 617d7a5, updated eb2d393)
  - [x] Simulate 10-second generation with progress milestones (0%, 25%, 50%, 75%, 90%, 100%)
  - [x] Progress updates include current_step, total_steps, progress_percent, estimated_seconds
  - [x] Generate mock GCS URL: gs://bucket/generations/gen-{id}.png
  - [x] Send completion with seed, steps, guidance_scale metadata

- [x] Comprehensive tests (Commit: eb2d393)
  - [x] Test inference progress webhook (payload structure, PATCH method)
  - [x] Test inference completed webhook (with/without metadata)
  - [x] Test inference failed webhook (error_code handling)
  - [x] Test error handling (connection failures)
  - [x] All 8 tests passing

**Exit Criteria**:
- [x] RabbitMQ consumer receives and processes messages
- [x] Webhook service sends callbacks matching API.md spec exactly
- [x] Mock generation completes with progress updates
- [x] All tests passing (8/8)

---

#### Phase 2: GPU Implementation (PLANNED)

**Status**: PLANNED
**Target Environment**: GCP Compute Engine with GPU

##### Subtasks

- [ ] Stable Diffusion inference
  - [ ] Load base model (Stable Diffusion v1.5)
  - [ ] Configure inference (50 steps, guidance_scale=7.5)
  - [ ] Support aspect ratios (1:1 [512×512px], 2:2 [1024×1024px], 1:2 [512×1024px])
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

**Implementation Reference**: [CODE_GUIDE.md#inference-pipeline](CODE_GUIDE.md#inference-pipeline)

**Exit Criteria**:
- [ ] Can generate image with LoRA in < 10 seconds
- [ ] Signature inserted correctly
- [ ] Generated images show style characteristics

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
