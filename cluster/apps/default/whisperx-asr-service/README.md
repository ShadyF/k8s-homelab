# WhisperX ASR service

> **Alpha / private-lab service.** This is an internal-only deployment for this
> cluster, not a hardened or multi-tenant transcription service.

`whisperx-asr-service` runs one CUDA-backed WhisperX API pod on `k8-w5`. That
node has an NVIDIA GTX 1660 SUPER with 6 GiB VRAM. It uses the normal image,
not a Blackwell image: the GTX 1660 SUPER is a Turing-generation GPU and does
not support the Blackwell-specific CUDA target.

## Egyptian Turbo configuration

The proposed GitOps configuration uses
`ghcr.io/shadyf/whisperx-asr-service:0.4.8` with `pullPolicy: IfNotPresent`
for both the main container and NLTK init container through the shared image
anchor. The standard variant matches the GTX 1660 SUPER; `0.4.8-blackwell`
is for RTX 50xx GPUs. See the versioned
[Egyptian Turbo recipe](https://github.com/ShadyF/whisperx-asr-service/tree/v0.4.8#egyptian-turbo-opt-in).

Deployment requires explicit approval. Do not merge, apply, reconcile, or restart
the deployment before approval. Keep one replica with the `Recreate` strategy;
the upgrade replaces the existing pod rather than running a parallel GPU pod.

```yaml
ASR_BACKEND: "whisper"
DEFAULT_MODEL: "mohammedaly22/whisper-large-v3-turbo-egyptian-code-switching"
PRELOAD_MODEL: "mohammedaly22/whisper-large-v3-turbo-egyptian-code-switching"
DEVICE: "cuda"
COMPUTE_TYPE: "int8_float16"
WHISPER_DECODE_MODE: "native"
VAD_METHOD: "silero"
VAD_CHUNK_SIZE: "20"
VAD_ONSET: "0.5"
WHISPER_BEAM_SIZE: "8"
WHISPER_NATIVE_BEST_OF: "5"
WHISPER_NATIVE_TEMPERATURES: "0.0,0.2,0.4,0.6,0.8,1.0"
WHISPER_NATIVE_CONDITION_ON_PREVIOUS_TEXT: "false"
NO_SPEECH_THRESHOLD: "0.8"
LOG_PROB_THRESHOLD: "-0.8"
COMPRESSION_RATIO_THRESHOLD: "2.4"
CACHE_DIR: "/.cache"
TORCH_HOME: "/.cache/torch"
```

`OPENAI_WHISPER1_MODEL` is unset so `whisper-1` follows `DEFAULT_MODEL`.
There is no model allowlist; the Egyptian identifier and `large-v3` remain
selectable. Omit request `language` for automatic detection. CPU alignment,
diarization, speaker resegmentation, and the existing `HF_TOKEN` Secret reference
are preserved. Native decoding ignores the retained `BATCH_SIZE: "2"`;
Silero ignores the retained `VAD_OFFSET: "0.363"`.

`PRELOAD_MODEL` prepares and loads the Egyptian model during startup. An
uncached startup downloads pinned original weights and converts them once on CPU,
then subsequent starts reuse valid
completed conversions from the persistent cache. This needs several GB free
for source weights, staging, and output, not just the approximately 819 MB
converted artifact. CPU/RAM requirements and first-load duration have not been
measured. The retained main-container requests are 2 CPU / 8 GiB RAM and limits
are 6 CPU / 10 GiB RAM; these are not validated conversion sizing.

Silero also downloads into the persisted Torch Hub cache at `/.cache/torch`.
Startup requires network access unless all needed assets are already cached.
A healthy endpoint does not establish successful Egyptian model preparation.
No transcription, inference, conversion-as-test, benchmarks, or GPU smoke tests
are part of pre-deployment verification.

## Capacity and retained settings

- The service keeps simple serving mode, one GPU worker, CPU alignment, and
  CUDA `int8_float16`. Release-specific GPU fit has not been established.
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

### Startup budget and deployment checks

The startup probe allows approximately 20 minutes (120 failures at 10-second
intervals). Kubernetes defers liveness and readiness probes until startup passes,
so liveness does not repeatedly kill a model still preparing within that budget.
The Deployment progress deadline is 25 minutes and the Helm timeout is 30 minutes,
leaving additional time for scheduling, image pulls, and NLTK initialization.
These are operational limits, not measured preparation times or a
guarantee that conversion fits. A longer failed rollout also delays remediation.

Before approval, check current node CPU/RAM availability, cache free space,
read/write access for the service user, and egress policies. Keep several GB
free beyond the completed artifact; if space is insufficient, stop and propose
a storage change without deleting data or using another PVC. The release
Dockerfile defaults to root; preserve the existing security settings and check
the actual runtime user after deployment.

Read-only inspection on 2026-11-11 confirmed the GTX 1660 SUPER and writable
cache access as UID 0. The 30 GiB cache had about 6.5 GiB free. This is several
GB of headroom, but does not establish peak preparation-space requirements.
The node had 8 CPU and approximately 30.3 GiB allocatable RAM; observed usage
was 1.475 CPU and 13,988 MiB RAM. Scheduled requests consumed 78% of CPU and
76% of RAM, including this service. Limits are overcommitted, so current idle
capacity is not guaranteed during concurrent load. Preserve the existing
2 CPU / 8 GiB requests and 6 CPU / 10 GiB limits pending actual startup evidence.

Initial preparation needs DNS and HTTPS access to Hugging Face and its download
hosts, plus GitHub/Torch Hub for Silero. Existing cache contents alone do not
establish network access for missing assets. The repository's NetworkPolicies
do not select this workload or restrict its egress; live policies confirmed this
on 2026-11-11. DNS/HTTPS reachability and external network controls were not tested.

After an approved rollout, inspect startup logs for all of these messages using
the full Egyptian model ID:

- `startup: preloading model <id>`
- `Model <id> loaded successfully`
- `startup: preloaded model <id>`

`startup: failed to preload model '<id>': ...` means preload failed even when
the pod becomes Ready. The application logs preload failures and continues
serving. Record whether preparation created or reused a completed conversion;
do not treat a healthy endpoint as evidence of successful model loading.
Do not run inference, benchmarks, or model-quality evaluations for verification.

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

The complete pre-upgrade HelmRelease is recorded in Git at
`23fac51e0894c4b09d80666473b55b7b506f8b6e`, path
`cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml`.
It includes image tag `egyptian-turbo-test`, `pullPolicy: IfNotPresent`, the entire
previous environment (including empty `PRELOAD_MODEL`), Secret references, probes,
resources, security settings, and persistent-volume mounts. There is no token
value in this HelmRelease; retain the existing encrypted Secret unchanged.

1. Inspect the complete saved configuration from the repository root:

   ```sh
   git show 23fac51e0894c4b09d80666473b55b7b506f8b6e:cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml
   ```

2. Prepare the rollback by restoring the **whole** HelmRelease, not just its
   image tag. This replaces any intervening edits to this file; review those
   edits before running it:

   ```sh
   git restore --source=23fac51e0894c4b09d80666473b55b7b506f8b6e -- cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml
   git diff -- cluster/apps/default/whisperx-asr-service/whisperx-asr-service-helm-release.yaml
   ```

3. Render and validate the restored configuration. Verify both containers use
   `ghcr.io/shadyf/whisperx-asr-service:egyptian-turbo-test`, `PRELOAD_MODEL` is
   empty, and the previous environment and timeout settings are restored. After explicit approval,
   submit the rollback through the normal GitOps review and deployment process.

Keep PVC `whisperx-asr-service-cache` and its contents throughout rollback.
Do not delete cache entries or repurpose another PVC. Image-only rollback leaves
startup preloading enabled and is not sufficient. The previous candidate tag is
mutable: record the live imageID before deployment if exact binary rollback is
required; restoring the tag alone cannot guarantee identical image contents.
