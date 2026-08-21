# M1-T04 narration and answer TTS spike

## Decision

Use OpenRouter's synchronous `POST /api/v1/audio/speech` endpoint with
`microsoft/mai-voice-2`, explicit MP3 output, speed `1.0`, and no expressive style for the V0
baseline. Select `en-US-Harper:MAI-Voice-2` as the initial voice. It is the best fit
because Microsoft identifies MAI-Voice-2 as its quality-oriented long-form model, Harper supports
the required U.S. English locale, and Harper delivered the shortest comparison sample without a
request-latency penalty that matters to V0. On 2026-08-21, a human listener compared Harper, Ethan,
and Olivia and selected Harper. The listener confirmed that the Harper source passage and detailed
answer were intelligible, stable, and comfortable for continued listening, with no material
pronunciation or pacing issues.

On 2026-08-21, all five live requests returned HTTP 200 and browser-playable MP3 audio on the first
attempt. The selected-voice source passage produced 39.000 seconds of audio in 1.476 seconds. A
2,339-character detailed answer produced 150.912 seconds of continuous audio in 4.187 seconds,
with no truncation or decoding failure.

## Selected request contract

| Item | Value |
| --- | --- |
| Endpoint | `POST https://openrouter.ai/api/v1/audio/speech` |
| Model | `microsoft/mai-voice-2` |
| Initial voice | `en-US-Harper:MAI-Voice-2` |
| Request body | JSON `model`, complete `input`, explicit `voice`, `response_format: "mp3"`, and `speed: 1.0` |
| Azure style | Omitted; no `provider.options.azure` block in the baseline |
| Expected response | Raw audio bytes with `Content-Type: audio/mpeg`; `X-Generation-Id` is retained for diagnostics when present |
| Live timeout | 120 seconds per attempt |
| Retry policy | One bounded retry for network/timeout, `429`, `500`, `502`, `503`, `524`, or `529`; no retry for other 4xx responses |

OpenRouter documents MP3 and PCM output, raw response bytes, the generation ID header, Azure-style
MAI voice names, speed `0.5`–`2.0`, and optional Azure `style`/`styledegree` controls. Microsoft
documents MAI-Voice-2 as the high-fidelity variant intended for long-form narration and lists the
tested U.S. English voices.

Sources:

- <https://openrouter.ai/docs/guides/overview/multimodal/tts>
- <https://openrouter.ai/docs/api/api-reference/speech/create-audio-speech>
- <https://openrouter.ai/microsoft/mai-voice-2>
- <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-voices>

## Inputs and measurements

The comparison text deliberately includes constitutional vocabulary, structural labels, a
fraction, and closely related multisyllabic words. The source passage is the benchmark's Article I
bill-process passage. The long answer explains that passage, distinguishes source wording from
interpretation, and labels its invented example.

| Input | Voice | Characters | Request latency | Audio duration | Size |
| --- | --- | ---: | ---: | ---: | ---: |
| Comparison | Harper | 420 | 2.122 s | 26.016 s | 520,320 B |
| Comparison | Ethan | 420 | 1.821 s | 31.584 s | 631,680 B |
| Comparison | Olivia | 420 | 1.457 s | 30.240 s | 604,800 B |
| Article I source passage | Harper | 647 | 1.476 s | 39.000 s | 780,000 B |
| Detailed explanatory answer | Harper | 2,339 | 4.187 s | 150.912 s | 3,018,240 B |

Median request latency was 1.821 seconds and the maximum was 4.187 seconds. Every output was a
24,000 Hz, mono, constant-160-kbps MP3. Every request completed in one attempt and returned an
`X-Generation-Id`. These are five point measurements, not provider latency guarantees.

The 2,339-character request is the longest input verified by this spike. Neither OpenRouter page
cited above states a model-specific maximum input length, so V0 must not treat this measurement as
the provider limit. Margin generates audio per authoritative paragraph or stored answer rather than
requesting full-book audio. A later live smoke test should retain explicit timeouts and surface a
clear error if an input accepted by application limits is rejected upstream.

## Browser playback verification

The selected Harper passage and detailed answer were served from localhost and loaded in the Codex
in-app target browser. Both reached media `readyState` 4 with their full expected durations and no
decode error. The passage advanced to 17.638 seconds. Starting the answer paused the passage, and
the answer advanced to 1.503 seconds. This establishes browser playability for the returned MP3
bytes and the separate narration/answer playback boundary.

## Human listening verification

On 2026-08-21, a human listener played the three voice-comparison files, the Harper source passage,
and the complete 150.912-second Harper answer. Harper was preferred over Ethan and Olivia. The
listener found the passage and answer intelligible, stable, and comfortable for continued
listening, with no material pronunciation or pacing problems. This confirms the selected voice and
the continued-listening acceptance criterion. The generated files remain under ignored
`var/spikes/m1-t04/` for later reproduction.

## Cache invalidation and configuration

The audio cache version must include every synthesis setting that can alter audio:

- request-contract or synthesis-prompt version;
- OpenRouter TTS model ID;
- exact voice ID;
- response format;
- synthesis speed;
- Azure style and style degree, including their explicit absence in the baseline.

The spike serializes those settings canonically and hashes them. The selected baseline currently
produces config version `cac618e44368569c`. Authoritative text is addressed separately by the
paragraph or interaction whose cache path contains this version. Changing a model, voice, format,
speed, style, style degree, or request construction must generate a new version and therefore a new
cache path. Browser playback speed is client state and does not invalidate synthesized audio.

Application configuration therefore needs at least `OPENROUTER_TTS_MODEL`,
`OPENROUTER_TTS_VOICE`, and an application-owned `TTS_CONFIG_VERSION` derived from the complete
settings above. `OPENROUTER_API_KEY` remains backend-only. The production boundary must validate
`audio/mpeg` and non-empty bytes before publishing a cache file and may record generation ID,
latency, byte count, and error code without logging the input passage or answer.

## Failure and retry behavior

The committed self-test proves that the spike retries each documented transient status (`429`,
`500`, `502`, `503`, `524`, and `529`) exactly once and does not retry a simulated `400`.
Production should use the same bounded classification:

| Condition | Behavior |
| --- | --- |
| Invalid input, voice, or request (`400`) | Non-retryable configuration/input error |
| Missing or invalid credential (`401`) | Non-retryable backend configuration error; never expose credential material |
| Insufficient credit (`402`) | Non-retryable billing/configuration error |
| Unknown model or route (`404`) | Non-retryable configuration error |
| Rate limit (`429`) | Retryable once with bounded delay |
| Provider/network failure (`500`, `502`, `503`, `524`, `529`, timeout) | Retryable once, then expose a retryable application error |
| Empty bytes, wrong content type, or undecodable success body | Reject the cache artifact and expose an upstream failure |

Narration and answer audio are disposable. A failed synthesis must not alter paragraph position or
duplicate a stored interaction; a later request regenerates audio from the authoritative stored
text.

## Reproduction

Run from the repository root. Generated audio and result JSON remain ignored under `var/`.

```sh
python3 -m py_compile docs/spikes/m1-t04_tts.py
python3 docs/spikes/m1-t04_tts.py self-test
OPENROUTER_API_KEY="$(sed -n 's/^OPENROUTER_API_KEY=//p' .env)" \
  python3 docs/spikes/m1-t04_tts.py synthesize var/spikes/m1-t04
```

The live run used macOS system Python 3.9.6 because the installed framework Python 3.13 certificate
store could not validate the endpoint chain. The script uses standard-library features compatible
with the project's required CPython 3.12. The credential is accepted only through the environment
and is not written to results, logs, source files, or browser-visible configuration.

## Scope boundary

This spike does not generate full-book audio, clone a voice, add application caching, implement the
production OpenRouter module, or introduce advanced prosody controls. No follow-up ticket is needed
from the measured endpoint behavior. Browser playback and human listening verification are complete.
