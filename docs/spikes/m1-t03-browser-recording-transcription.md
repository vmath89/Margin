# M1-T03 browser recording and transcription spike

## Decision

Use Chromium-produced WebM/Opus directly with OpenRouter's synchronous transcription endpoint; no
format conversion is required for the verified Chromium path. A Chromium 151 `MediaRecorder` blob
containing the B1 utterance was accepted by `openai/gpt-4o-transcribe` on 2026-08-21 with HTTP 200,
0% word error rate, and 1.182 seconds end-to-end latency. Five clean representative Constitution
questions also returned HTTP 200 with a maximum word error rate of 7.69%, median latency of 0.971
seconds, and maximum latency of 2.241 seconds. A 119.008-second boundary fixture returned HTTP 200
in 2.081 seconds, supporting the configured 120-second V0 recording limit with a one-second stop
margin.

## Selected request contract

| Item | Value |
| --- | --- |
| Endpoint | `POST https://openrouter.ai/api/v1/audio/transcriptions` |
| Model | `openai/gpt-4o-transcribe` |
| Request body | JSON with base64 `input_audio.data`, `input_audio.format: "webm"`, `language: "en"`, and `temperature: 0` |
| Browser upload MIME type | `audio/webm` or `audio/webm;codecs=opus`; the backend must validate the media type and send OpenRouter the format value `webm` |
| V0 maximum recording duration | Stop at 120 seconds and accept only files measured at no more than 120 seconds; a 119.008-second WebM/Opus fixture was accepted in 2.081 seconds. This is an application limit, not a claimed provider hard limit. |
| Spike client timeout | 60 seconds per request |
| Spike retries | None, so observed latency is one end-to-end request; production keeps the architecture's one bounded retry for transient failures |

OpenRouter's current STT guide lists WebM (`audio/webm`) among the common accepted formats, while
noting that support can vary by model/provider. Its current filtered model catalog includes
`openai/gpt-4o-transcribe`. The endpoint returns transcript text and usage data in one synchronous
JSON response and identifies the request with `X-Generation-Id` when present.

Sources:

- <https://openrouter.ai/docs/guides/overview/multimodal/stt>
- <https://openrouter.ai/docs/api/api-reference/transcriptions/create-audio-transcriptions>
- <https://openrouter.ai/api/v1/models?output_modalities=transcription>

## Representative recordings

The spike covers the five speech-input shapes required by M1-T03, an actual browser encoder path,
and the configured duration boundary:

| Fixture | Benchmark role |
| --- | --- |
| `local-passage.webm` | Local passage explanation, based on B1 |
| `current-section.webm` | Current-section synthesis, based on B5 |
| `document-wide.webm` | Explicit document-wide scope |
| `same-episode-follow-up.webm` | Follow-up wording from S2 |
| `later-episode-continuity.webm` | Reference to an earlier episode from S3 |
| `browser-local-passage.webm` | B1 speech re-encoded by Chromium 151 `MediaRecorder` as `audio/webm;codecs=opus` |
| `duration-boundary.webm` | B1 speech followed by encoded silence to reach 119.008 seconds and exercise the configured maximum |

The committed script uses macOS `say` to produce deterministic speech and FFmpeg to encode the five
clean 48 kHz mono WebM/Opus fixtures. The committed capture page then decodes B1 in Web Audio and
records the resulting `MediaStream` through the browser's own `MediaRecorder`; it does not use
FFmpeg to create `browser-local-passage.webm`. This separates provider accuracy evidence from the
browser encoder/muxer compatibility check without creating recording UI.

Generated recordings, manifests, and live results remain under ignored `var/spikes/m1-t03/`; no
question audio is persisted as application data or committed. The fixtures do not measure physical
microphone noise, accents, permission UX, or mobile hardware. Those variables remain target-browser
manual testing for the later recording UI, while this spike establishes the direct Chromium
WebM/Opus transport path.

## Reproduction

Run from the repository root:

```sh
python3 docs/spikes/m1-t03_transcribe.py self-test
python3 docs/spikes/m1-t03_transcribe.py prepare var/spikes/m1-t03
python3 docs/spikes/m1-t03_transcribe.py prepare-duration-probe var/spikes/m1-t03
python3 docs/spikes/m1-t03_transcribe.py serve-browser-capture var/spikes/m1-t03
# Open http://127.0.0.1:8765 and press "Capture benchmark utterance".
OPENROUTER_API_KEY="$(sed -n 's/^OPENROUTER_API_KEY=//p' .env)" \
  python3 docs/spikes/m1-t03_transcribe.py \
  transcribe var/spikes/m1-t03 > var/spikes/m1-t03/live-results.json
OPENROUTER_API_KEY="$(sed -n 's/^OPENROUTER_API_KEY=//p' .env)" \
  python3 docs/spikes/m1-t03_transcribe.py transcribe-one \
  var/spikes/m1-t03/browser-local-passage.webm --question-type local-passage \
  > var/spikes/m1-t03/browser-live-result.json
OPENROUTER_API_KEY="$(sed -n 's/^OPENROUTER_API_KEY=//p' .env)" \
  python3 docs/spikes/m1-t03_transcribe.py transcribe-one \
  var/spikes/m1-t03/duration-boundary.webm --question-type local-passage \
  > var/spikes/m1-t03/duration-boundary-live-result.json
```

The API key is accepted only through the environment. Do not put a real key in this report, a
command committed to the repository, frontend configuration, or browser-visible output.

## Local media verification

Local generation on 2026-08-21 produced five non-empty WebM files. `ffprobe` identified every
audio stream as Opus, 48,000 Hz, mono, and every duration was below the configured 120-second V0
limit. The generated boundary probe was WebM/Opus, 48,000 Hz mono, 119.008 seconds, and 381,851
bytes.

The Chromium capture reported `audio/webm;codecs=opus`; `ffprobe` identified WebM/Opus, 48,000 Hz
stereo, 5.277 seconds, and 85,441 bytes. Chromium's blob omitted container-level duration metadata,
an actual browser-specific difference missed by the FFmpeg fixtures. The verifier now derives a
missing duration from audio-packet timestamps before enforcing the maximum. Exact file hashes and
metadata remain in ignored generated manifests so the report does not pretend deterministic audio
bytes across OS voice or browser releases.

## Live transcript and latency results

The script defines acceptable fixture accuracy as word error rate at or below 10% for every
question. All five results passed that threshold and a manual comparison confirmed that every
meaning-bearing term required to select and answer the benchmark scope remained usable.

| Question type | Observed transcript difference | WER | Latency |
| --- | --- | ---: | ---: |
| Local passage | Case-only `Preamble` difference | 0% | 2.241 s |
| Current section | Spoken `Article One` normalized to `Article I` | 3.70% | 0.971 s |
| Document-wide | Possessive `text's structural` rendered as `text-structural`; scope and subject remained unambiguous | 7.69% | 0.920 s |
| Same-episode follow-up | Exact normalized transcript | 0% | 0.920 s |
| Later-episode continuity | Case-only `Preamble` difference and `Article One` normalized to `Article I` | 3.12% | 1.253 s |

Each request used one attempt and returned HTTP 200, transcript text, token usage, cost, and an
`X-Generation-Id`. Median wall latency was 0.971 seconds and maximum wall latency was 2.241 seconds.
Reported aggregate cost for the five requests was USD 0.00218. The provider did not return an
audio-duration usage field for this model; fixture duration therefore comes from local `ffprobe`
measurement.

The Chromium `MediaRecorder` B1 fixture returned the expected normalized transcript at 0% WER in
1.182 seconds and cost USD 0.00036. The 119.008-second boundary fixture returned the same expected
transcript at 0% WER in 2.081 seconds and cost USD 0.003205. Both used one attempt, returned HTTP
200, and completed within the configured 60-second timeout.

The live commands exit with status 2 when any result exceeds the 10% WER threshold; emitting
`all_acceptable: false` in JSON is no longer treated as successful verification.

Local compilation, fixture generation, decoding, and metric tests used the installed framework
Python 3.13. The live requests used macOS system Python 3.9.6 because the framework installation's
local certificate store could not validate the endpoint chain. The script uses only standard
library features compatible with the project's specified CPython 3.12 runtime; the certificate
issue is machine-local and does not require an application workaround.

## Browser constraints

- Before constructing `MediaRecorder`, the web app must test
  `MediaRecorder.isTypeSupported("audio/webm;codecs=opus")`; it must not relabel an unsupported
  browser's output as WebM.
- Chromium 151's emitted `audio/webm;codecs=opus` blob was accepted directly. WebM/Opus recording
  is also available in current Firefox families and was added to Safari's `MediaRecorder` in Safari
  18.4, but those encoder outputs were not submitted in this run. A browser that fails the runtime
  MIME check must receive a clear unsupported-recording error. If target-browser testing finds
  conversion necessary, it requires a separate ticket.
- Microphone capture requires user permission and a secure context. Localhost is permitted for
  development; remote use requires HTTPS, matching `ARCHITECTURE.md`.
- Stop the recorder at 120 seconds and reject empty, over-duration, non-WebM, or non-Opus input
  before making a provider request. The question audio remains temporary and is deleted according
  to the architecture's interaction flow.

Browser references:

- <https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static>
- <https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia>
- <https://webkit.org/blog/16574/webkit-features-in-safari-18-4/>

## Error behavior and retry boundary

The backend integration must map provider failures into the stable API error shape without logging
audio or credentials:

| Condition | Behavior |
| --- | --- |
| Unsupported/invalid audio or request (`400`) | Non-retryable; ask the user to record again after local validation details are handled |
| Missing/invalid backend credential (`401`) | Non-retryable configuration error; never expose credential material |
| Insufficient provider credit (`402`) | Non-retryable configuration/billing error |
| Unknown/unavailable model (`404`) | Non-retryable configuration error |
| Rate limit (`429`) | Retryable; production may perform the architecture's one bounded retry |
| Provider/network failure (`500`, `502`, `503`, timeout) | Retryable; production may perform one bounded retry, then preserve the reading position and allow a fresh Ask |
| Empty or malformed success body | Treat as retryable upstream failure; do not create a textual interaction |

Transcription and reasoning later share one user-visible request, but the temporary recording must
not create or duplicate an `Interaction` until both transcript and answer succeed. This spike does
not implement that application flow.

## Scope boundaries and follow-up decision

This ticket does not create recording UI, persistence, streaming, voice activity detection, or
long-recording segmentation. No format-conversion ticket is created yet: current target formats
have a direct WebM/Opus path, and conversion would be speculative until a target browser fails the
runtime check. If that happens, add an explicit backlog ticket rather than hiding conversion in the
recording or OpenRouter boundary.
