# WhisperX ASR service

> **Alpha / private-lab service.** This is an internal-only deployment for this
> cluster, not a hardened or multi-tenant transcription service.

`whisperx-asr-service` runs one CUDA-backed WhisperX API pod on `k8-w5`. That
node has an NVIDIA GTX 1660 SUPER with 6 GiB VRAM. It uses the normal image,
not a Blackwell image: the GTX 1660 SUPER is a Turing-generation GPU and does
not support the Blackwell-specific CUDA target.

## Configuration and capacity

- The service uses CUDA with `int8_float16`, `large-v3`, simple serving mode,
  one GPU worker, batch size 1, and CPU alignment. This experimental compute
  type reduces model memory on the 6 GiB GPU; use `large-v3-turbo` if memory,
  speed, or transcription quality is unacceptable.
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
- `large-v3` is preloaded. Models remain loaded for 900 seconds (15
  minutes) and the eviction loop runs every 60 seconds. Expect a cold start
  after eviction, after a restart, or when the cache is not yet populated.
- Uploads are limited to 400 MiB, but the service handles uploads in memory.
  A 400 MiB input can therefore consume substantially more pod memory during
  decoding and processing.

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

## Verification and troubleshooting

After Flux reconciles the manifests and the encrypted Secret exists, use:

```sh
kubectl -n default get helmrelease whisperx-asr-service
kubectl -n default get pods -l app.kubernetes.io/instance=whisperx-asr-service -o wide
kubectl -n default describe pod -l app.kubernetes.io/instance=whisperx-asr-service
kubectl -n default logs -l app.kubernetes.io/instance=whisperx-asr-service --all-containers
kubectl -n default get svc,servicemonitor whisperx-asr-service
kubectl -n default run whisperx-health --rm -it --restart=Never --image=curlimages/curl \
  -- curl -fsS http://whisperx-asr-service.default.svc.cluster.local:9000/health
```

For `Pending`, confirm `k8-w5` has an available time-sliced GPU slot and that
the pod requests `nvidia.com/gpu: 1`. For startup probe failures, inspect logs
for image pulls, Hugging Face gated-model acceptance, token errors, download
failures, or preload time. For CUDA OOMs, reduce concurrency or batch size,
choose a smaller model, and check the other three time-sliced GPU consumers.
