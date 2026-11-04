# WhisperX ASR service

> **Alpha / private-lab service.** This is an internal-only deployment for this
> cluster, not a hardened or multi-tenant transcription service.

`whisperx-asr-service` runs one CUDA-backed WhisperX API pod on `k8-w5`. That
node has an NVIDIA GTX 1660 SUPER with 6 GiB VRAM. It uses the normal image,
not a Blackwell image: the GTX 1660 SUPER is a Turing-generation GPU and does
not support the Blackwell-specific CUDA target.

## Manual Egyptian Turbo trial

The proposed GitOps configuration uses
`ghcr.io/shadyf/whisperx-asr-service:egyptian-turbo-test` with `pullPolicy: IfNotPresent`
for both the main container and NLTK init container through the shared image
anchor. This is a moving candidate tag, not an immutable release: nodes reuse
cached images and only pull the current candidate when it is absent. See the upstream
[Egyptian Turbo recipe](https://github.com/ShadyF/whisperx-asr-service/blob/feature/egyptian-turbo/README.md#egyptian-turbo-opt-in).

Deployment requires explicit approval. Do not merge, apply, reconcile, or restart
the deployment before approval. Keep one replica with the `Recreate` strategy;
the trial replaces the existing pod rather than running a parallel GPU pod.

```yaml
ASR_BACKEND: whisper
DEFAULT_MODEL: mohammedaly22/whisper-large-v3-turbo-egyptian-code-switching
PRELOAD_MODEL: ""
DEVICE: cuda
COMPUTE_TYPE: int8_float16
WHISPER_DECODE_MODE: native
VAD_METHOD: silero
VAD_CHUNK_SIZE: "20"
VAD_ONSET: "0.5"
WHISPER_BEAM_SIZE: "8"
WHISPER_NATIVE_BEST_OF: "5"
WHISPER_NATIVE_TEMPERATURES: "0.0,0.2,0.4,0.6,0.8,1.0"
WHISPER_NATIVE_CONDITION_ON_PREVIOUS_TEXT: "false"
NO_SPEECH_THRESHOLD: "0.8"
LOG_PROB_THRESHOLD: "-0.8"
COMPRESSION_RATIO_THRESHOLD: "2.4"
CACHE_DIR: /.cache
TORCH_HOME: /.cache/torch
```

`OPENAI_WHISPER1_MODEL` is unset so `whisper-1` follows `DEFAULT_MODEL`.
There is no model allowlist; the Egyptian identifier and `large-v3` remain
selectable. Omit request `language` for automatic detection. CPU alignment,
diarization, speaker resegmentation, and the existing `HF_TOKEN` Secret reference
are preserved. Native decoding ignores the retained `BATCH_SIZE: "2"`;
Silero ignores the retained `VAD_OFFSET: "0.363"`.

Empty `PRELOAD_MODEL` defers preparation to first use. The candidate downloads
pinned original weights and converts them once on CPU, then reuses valid
completed conversions from the persistent cache. This needs several GB free
for source weights, staging, and output, not just the approximately 819 MB
converted artifact. CPU/RAM requirements and first-load duration have not been
measured. The retained main-container requests are 2 CPU / 8 GiB RAM and limits
are 6 CPU / 10 GiB RAM; these are not validated conversion sizing.

Silero also downloads into the persisted Torch Hub cache at `/.cache/torch`.
First use requires network access unless all needed assets are already cached.
A healthy endpoint does not establish successful Egyptian model preparation.
No transcription, inference, conversion-as-test, benchmarks, or GPU smoke tests
are part of pre-deployment verification.

## Capacity and retained settings

- The service keeps simple serving mode, one GPU worker, CPU alignment, and
  CUDA `int8_float16`. GPU fit for this candidate has not been established.
- The NVIDIA device plugin exposes the physical GPU as four time-sliced
  `nvidia.com/gpu` slots. This pod requests one slot. Time slicing does **not**
  partition VRAM, so all four potential clients share the 6 GiB device memory
  and can cause GPU OOMs under simultaneous model loads.
- The request and limit for `nvidia.com/gpu` are both exactly `1`, as required
  for Kubernetes GPU scheduling. The existing cluster-wide time-slicing
  configuration is intentionally unchanged.
- A 30 GiB Longhorn RWO PVC persists `/.cache` for Hugging Face and model
  downloads. `/tmp` is a bounded 1 GiB `emptyDir` so uploads and temporary
  files can work while the container root filesystem stays read-only.
- Models remain loaded for 900 seconds (15 minutes) and the eviction loop
  runs every 60 seconds. Expect a cold load after eviction or a restart;
  completed on-disk conversion artifacts remain available for reuse.
- Uploads are limited to 400 MiB, but the service handles uploads in memory.
  A 400 MiB input can therefore consume substantially more pod memory during
  decoding and processing.

### Cache inspection: 2026-11-04 13:45 UTC

The existing 30 GiB PVC had 31,526,391,808 bytes total and 10,285,342,720 bytes
free (9.58 GiB) at `/.cache`, providing several GB of preparation headroom.
This is a point-in-time observation, not a measured peak-space requirement;
recheck before an approved trial. If several GB are no longer available, stop
and propose a storage change without deleting cache data or using another PVC.

The running service user was UID/GID `0:0`. The cache root and inspected model,
Torch Hub, NLTK, and Matplotlib directories were owned by `root:root`, mode
`755`, and passed runtime write-access checks. No probe files were created;
permissions were assessed without a write test. `/.cache/huggingface` did not
exist; `HF_HOME` remains `/.cache`. The mount was read-write `ext4` on the
Longhorn volume backing the existing PVC. The inspected candidate image config
also defaults to UID 0; its source-revision entrypoint does not switch users.
This supports cache permission compatibility, not successful model preparation.
Recheck image identity if the moving candidate tag changes.

## Internal API and monitoring

The HelmRelease creates only a ClusterIP Service; there is no ingress and no
Ray dashboard exposure. Reach it from workloads in the cluster at:

- `http://whisperx-asr-service.default.svc.cluster.local:9000`
- `http://whisperx-asr-service:9000` from the `default` namespace

The upstream API has no built-in authentication. With no NetworkPolicy, it is
reachable from every namespace in this cluster. Treat it and any uploaded audio
as private-lab resources.

Prometheus discovers `/metrics` over the named `http` port every minute, with a
10-second scrape timeout. Metrics reflect the upstream endpoint behavior; do
not assume OpenAI-compatible API requests are individually instrumented or
represented in request metrics until verified against the running image.

## Hugging Face token and gated models

The required Secret is named `whisperx-asr-service` and must contain the
`HF_TOKEN` key. An empty `secrets.enc.yaml` template is included. Fill and
encrypt it before committing or allowing Flux to reconcile the app.

Before creating the Secret, sign in to Hugging Face with the token owner and
accept the gated-model terms for all three Pyannote models used by diarization:

- `pyannote/speaker-diarization-community-1`
- `pyannote/segmentation-3.0`
- `pyannote/speaker-diarization-3.1`

From this directory, fill `stringData.HF_TOKEN` in `secrets.enc.yaml`, then
encrypt the file before it is staged, committed, or reconciled:

```sh
sops --encrypt --in-place secrets.enc.yaml
git add secrets.enc.yaml
```

Do not commit the template while it is empty or after adding a plaintext token.
The empty value lets the pod start, but diarization will not work until a valid
token is encrypted and reconciled.

## Read-only inspection and troubleshooting

These commands inspect the existing service without starting workloads:

```sh
kubectl -n default get helmrelease whisperx-asr-service
kubectl -n default get pods -l app.kubernetes.io/instance=whisperx-asr-service -o wide
kubectl -n default describe pod -l app.kubernetes.io/instance=whisperx-asr-service
kubectl -n default logs -l app.kubernetes.io/instance=whisperx-asr-service --all-containers
kubectl -n default get svc,servicemonitor whisperx-asr-service
```

For `Pending`, confirm `k8-w5` has an available time-sliced GPU slot and that
the pod requests `nvidia.com/gpu: 1`. For startup probe failures, inspect logs
for image pulls, Hugging Face gated-model acceptance, token errors, download
failures, or model-load errors. For CUDA OOMs, check the other time-sliced GPU
consumers; native decoding does not use batch size. Any configuration change
requires separate approval.

## Rollback: restore image and complete configuration

The complete pre-trial HelmRelease is recorded in Git at
`79744f75048d6159b92fd7a4759b141015ad4915`, path
`cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml`.
It includes image tag `0.4.7`, `pullPolicy: IfNotPresent`, the entire previous
environment (including `PRELOAD_MODEL: large-v3`), Secret references, probes,
resources, security settings, and persistent-volume mounts. There is no token
value in this HelmRelease; retain the existing encrypted Secret unchanged.

1. Inspect the complete saved configuration from the repository root:

   ```sh
   git show 79744f75048d6159b92fd7a4759b141015ad4915:cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml
   ```

2. Prepare the rollback by restoring the **whole** HelmRelease, not just its
   image tag. This replaces any intervening edits to this file; review those
   edits before running it:

   ```sh
   git restore --source=79744f75048d6159b92fd7a4759b141015ad4915 -- cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml
   git diff -- cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml
   ```

3. Render and validate the restored configuration. Verify both containers use
   `ghcr.io/shadyf/whisperx-asr-service:0.4.7`, `PRELOAD_MODEL` is `large-v3`, and
   all Egyptian-only environment additions are gone. After explicit approval,
   submit the rollback through the normal GitOps review and deployment process.

Keep PVC `whisperx-asr-service-cache` and its contents throughout rollback.
Do not delete cache entries or repurpose another PVC. Image-only rollback leaves
trial model selection and decoder controls active and is not sufficient.
