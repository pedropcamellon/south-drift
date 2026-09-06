# Audio Transcription Microservice

## Overview

FastAPI microservice for audio transcription with **Abstract Provider Pattern** supporting self-hosted Whisper (implemented), AWS Transcribe, and Azure Speech (planned). Configuration-driven provider selection enables HIPAA compliance and cloud migration flexibility.

**Current Status**: Production-ready with self-hosted Whisper. Processes 1-3 second clinical voice notes in ~0.5-0.6 seconds.

**Design Philosophy**:

- **Vendor-agnostic**: Switch providers via environment variable
- **HIPAA-compliant**: Self-hosted Whisper keeps PHI on-premise (no BAA required)
- **Single-cloud deployment**: One active provider per instance
- **Migration-friendly**: Provider changes require only config updates

**Security Priority**: Clinical voice notes contain PHI. Self-hosted Whisper recommended for maximum security. AWS/Azure require Business Associate Agreements (BAA) for HIPAA compliance.

---

## Architecture

### Microservices Pattern

- **Decoupled**: Transcription service runs independently from main backend
- **Scalable**: Multiple transcription workers can run in parallel
- **Language-agnostic**: Backend can be any stack (currently Python FastAPI)
- **Storage-agnostic**: Works with presigned URLs from any storage provider

### Abstract Provider Pattern

Base interface (`TranscriptionProvider` ABC) ensures consistent behavior across vendors. Factory pattern manages provider lifecycle and singleton instances.

### Project Structure

```
services/transcribe/
├── Dockerfile              # Multi-stage build (whisper/aws/azure variants)
├── docker-compose.yml      # Local dev with watch mode
├── pyproject.toml          # uv-based dependencies
├── app/
│   ├── main.py             # FastAPI app with /transcribe and /health endpoints
│   ├── config.py           # Settings (TRANSCRIPTION_PROVIDER, model size, device)
│   ├── models.py           # Pydantic request/response schemas
│   └── providers/
│       ├── __init__.py     # Public API (get_transcription_provider)
│       ├── base.py         # TranscriptionProvider ABC
│       ├── whisper.py      # faster-whisper implementation (IMPLEMENTED)
│       ├── aws.py          # AWS Transcribe (Planned)
│       ├── azure.py        # Azure Speech (Planned)
│       └── factory.py      # Singleton provider factory
└── tests/
    └── test_providers.py
```

### Provider Interface Design

All providers implement `TranscriptionProvider` abstract base class with single method:

- `async def transcribe() → dict`: Downloads audio via presigned URL, processes, returns standardized response

Factory pattern (`get_transcription_provider()`) manages:

- Provider selection based on `TRANSCRIPTION_PROVIDER` environment variable
- Singleton instances (Whisper model loaded once, cached)
- Lazy initialization (model loads on first request, not startup)

### Configuration Strategy

Environment-driven provider selection:

- `TRANSCRIPTION_PROVIDER`: `whisper` (default), `aws`, `azure`
- Provider-specific settings: model size, device (CPU/GPU), region, API keys
- Docker build args select provider variant (reduces image size)

---

## API Endpoints

### POST /transcribe

Accepts presigned audio URL from any storage provider, returns transcript.

**Request**: JSON body with `audio_url` (presigned URL), optional `language_code`, `speaker_labels`, `vocabulary_name`

**Response**: JSON with `transcript` (string), `language_code`, `confidence`, `segments` (array), `processing_time`, optional `job_id`

**Storage Agnostic**: Works with MinIO, AWS S3, Azure Blob Storage presigned URLs. Service downloads audio via HTTP, no storage SDK dependencies required.

**Error Handling**: Returns 500 with error details in JSON (`error`, `detail`, `job_id`). Errors logged with full traceback for debugging.

### GET /health

Health check for Docker/Kubernetes orchestration. Returns provider name and model size.

### HEAD /health

Lightweight healthcheck for Docker HEALTHCHECK directive. Returns 200 OK with no body.

---

## Storage Access Strategy

**Implementation**: HTTP download from presigned URLs (storage-agnostic)

All three storage providers (AWS S3, Azure Blob, MinIO) generate presigned URLs with temporary access credentials. Transcription service downloads audio via standard HTTP GET - no storage-specific SDKs needed.

**Benefits**:

- Works with any storage provider (including CDNs, Cloudflare R2)
- No boto3/azure-storage-blob dependencies in transcription service
- Simpler container (fewer dependencies, faster builds)
- Backend controls access (generates presigned URLs with expiration)

**Flow**:

1. Backend uploads audio to storage (S3/Azure/MinIO)
2. Backend generates presigned URL (1-hour expiration)
3. Backend calls transcription service with presigned URL
4. Transcription service downloads via HTTP (httpx client)
5. Transcription service processes audio locally
6. Temp file cleaned up after processing

**Presigned URL Requirements**:

- Must be publicly accessible (no additional auth headers)
- 1-hour expiration (transcription completes in <1 minute)
- Supports byte-range requests (optional, for large files)

---

## Processing Workflow

### Implementation: Async Background Task

Backend returns 200 OK immediately after audio upload. Transcription runs in background via `asyncio.create_task()`. Frontend polls for updates.

**Flow**:

1. Frontend: User records audio → POST to backend with WebM blob
2. Backend: Upload to MinIO → Generate presigned URL → Return 200 OK
3. Backend (background task): Call transcription service with presigned URL
4. Transcription service: Download audio → Process with Whisper → Return transcript
5. Backend (background task): Update interaction note with timestamped transcript
6. Frontend: Poll GET `/api/interactions/{id}` every 2 seconds
7. Frontend: Detect `updatedAt` timestamp change or transcript in note → Stop polling → Update UI

**Timing** (1-3 second audio):

- Audio upload: <1 second
- Transcription processing: 0.5-0.6 seconds
- Total user wait: 2-4 seconds (includes frontend polling delay)

**Error Handling**:

- Background task catches exceptions, logs with traceback
- Error stored in `metadata.audio.transcriptionError`
- Frontend polling detects error state, displays to user

**Polling Optimization**:

- Max 5 attempts (10 second timeout)
- Stops immediately on: `updatedAt` change, note content change, or transcript marker detected
- Logs all errors to console (no silent failures)
- Detects transcription failures via metadata check

### Alternative: Message Queue (Future)

For long audio files (>5 minutes) or high-volume workloads, consider message queue pattern:

- Redis Streams, RabbitMQ, or AWS SQS
- Horizontal scaling with multiple transcription workers
- Webhook callbacks instead of polling
- Dead-letter queues for retry logic

**Current status**: Async background task sufficient for MVP (clinical voice notes are <2 minutes)

### Docker Architecture

**Multi-stage Dockerfile**:

1. Base stage: Python 3.11, system deps (ffmpeg, wget), uv
2. Provider stages: Install provider-specific deps (whisper/aws/azure)
3. Final stage: Copy app code, set healthcheck, expose port 8001

**Whisper Optimization**: Model cached in Docker image during build (base model ~150MB). First transcription uses cached model, no download delay.

**Healthcheck**: Docker uses `HEAD /health` (lightweight, no response body). Interval 30s, timeout 10s, start period 40s (model loading time).

---

## Provider Implementation Details

### Self-Hosted Whisper (Production Ready ✅)

**Technology**: faster-whisper (CTranslate2-optimized Whisper models)

**Configuration**:

- Model: `base` (74M parameters, good accuracy/speed balance)
- Device: `cpu` (works on standard hardware)
- VAD filter: Disabled (was removing audio from short clinical recordings)
- Word timestamps: Enabled (for segment granularity)

**Performance**:

- 1-second audio: ~0.5 seconds
- 3-second audio: ~0.6 seconds
- CPU usage: ~80-100% during transcription (single-threaded)

**Model Caching**: On first local startup, the model downloads into the named
`whisper-models` Docker volume at
`/workspace/services/transcribe/.cache/huggingface`. Later container restarts
and image rebuilds reuse that volume. The first startup requires network access
to Hugging Face; later startup does not, provided the volume is retained. The
`production` Docker target instead preloads the build-pinned
`WHISPER_MODEL_SIZE` into `/opt/whisper-cache`, so production startup does not
depend on a writable runtime cache volume.

**Language Support**: Auto-detect or specify language code (`en-US` → `en`). Supports 99 languages.

**No External Dependencies**: After the model cache is populated, transcription
runs locally without model-provider API credentials. Network access remains
necessary to retrieve the source audio and to initially populate a missing
model cache.

**Limitations**:

- No speaker diarization (planned via pyannote.audio)
- No confidence scores (Whisper doesn't provide)
- CPU-bound (GPU support requires CUDA drivers)

### AWS Transcribe (Planned)

**Setup Requirements**:

- AWS Business Associate Agreement (BAA) for HIPAA
- IAM user with `transcribe:*` permissions
- S3 bucket for temporary audio storage (if not using HTTPS URLs)

**Implementation Strategy**:

- Submit job via boto3 client
- Poll for completion (AWS doesn't provide sync API)
- Parse JSON response, map to standard format

**Trade-offs**: Higher accuracy, speaker diarization, custom medical vocabulary, but requires BAA and costs $0.024/minute.

### Azure Speech (Planned)

**Setup Requirements**:

- Azure Business Associate Agreement (BAA) for HIPAA
- Cognitive Services Speech resource
- API key and region

**Implementation Strategy**:

- Real-time streaming API (faster than batch)
- Speaker diarization available
- Custom medical terminology support

**Trade-offs**: Fast processing, good accuracy, but requires BAA and costs ~$0.02/minute.

---

## Provider Comparison

| Feature                 | Self-Hosted Whisper               | AWS Transcribe   | Azure Speech     |
| ----------------------- | --------------------------------- | ---------------- | ---------------- |
| **Status**              | Production Ready                  | Planned          | Planned          |
| **HIPAA Compliance**    | Built-in (no BAA)                 | Requires BAA     | Requires BAA     |
| **Setup Cost**          | $0                                | $0               | $0               |
| **Usage Cost**          | Infrastructure only (~$50-100/mo) | $0.024/minute    | $0.02/minute     |
| **Accuracy**            | Good (base model 85-90%)          | Excellent (95%+) | Excellent (95%+) |
| **Speed**               | 0.5-0.6s (1-3s audio)             | 5-15s            | 2-5s (streaming) |
| **Speaker Diarization** | No (planned)                      | Yes              | Yes              |
| **Custom Vocabulary**   | No                                | Yes              | Yes              |
| **Offline Support**     | Yes                               | No               | No               |
| **Languages**           | 99 languages                      | 30+ languages    | 100+ languages   |

**Recommendation**: Whisper for MVP and HIPAA compliance. Consider AWS/Azure for higher accuracy requirements or speaker diarization needs (after signing BAA).

---

## Technical Decisions & Rationale

### VAD Filter Disabled

**Issue**: Voice Activity Detection (VAD) was removing 100% of audio from short clinical voice notes (1-3 seconds).

**Symptom**: Logs showed "VAD filter removed 00:01.260 of audio" for 1.26-second files → zero segments → empty transcript.

**Root Cause**: Aggressive VAD settings classified short recordings as non-speech, especially with:

- WebM format (Whisper prefers WAV/MP3)
- Quiet/soft-spoken recordings
- Background noise misclassified

**Solution**: Set `vad_filter=False` in faster-whisper. Trade-off: May transcribe background noise, but ensures all speech captured.

**Alternative Considered**: Tune VAD threshold (rejected - unreliable for short clips).

### Overwrite Note Strategy

**Implementation**: Each new transcript replaces interaction note completely (with timestamp).

**Rationale**:

- Simplifies UX (one current transcript visible)
- Avoids duplicate accumulation
- Clinical workflow: Latest voice note is most relevant

**Trade-off**: Previous transcripts lost (in-memory storage issue). Phase 2 PostgreSQL migration will enable transcript history.

### Smart Polling

**Optimization**: Frontend stops polling on first success (checks `updatedAt` timestamp + transcript marker).

**Problem Solved**: Was polling 10 times even when transcript ready after first poll.

**Implementation**: Compare `updatedAt`, note content, and check for `[Audio Transcript` marker. Stops immediately on any match.

**Performance**: Typical flow now 1-2 polls (2-4 seconds) instead of 10 polls (20 seconds).
