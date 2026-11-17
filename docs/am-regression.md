# Aviation AM regression: withdrawal and rollback

## User observation

After installing the AM Hotfix `527f5229`, the user reports worse audio than before, described as crunchy and
overloaded. There is no controlled audio recording or receiver-register trace of this observation. The report
does not establish whether squelch 0 changes it.

The AM backport changed the filter, demodulator output/control, gain loop and squelch together. Host logic tests
and an upstream bench report did not establish that those combined settings improved audio on the affected radio.

## Mitigation

- Mark `v2026.11.15-527f5229` as a withdrawn prerelease and restore the previous stable release in the installer.
- Revert the entire `0028-am-strong-signal-agc.patch` backport. Do not guess another combination of unmeasured AM
  register settings for a public release.
- Keep the existing DMR PTT/abort correction, custom boot picture, and FM/DMR/P25/NXDN VFO.
- The rollback's receiver, UI and digital-voice source files match `b736e952`; only documentation and the build
  identity differ. This restores the previous AM behavior, including its original limitations.

## Diagnostic model, not an RF/audio measurement

The withdrawn gain loop averages consecutive RSSI values without accounting for a gain change between them.
For example, a reading of 222 reduces gain by 32 dB; an immediate next reading of 142 is averaged with 222 and
causes another 13 dB reduction. The previous host test explicitly expected that extra cut rather than checking
the closed-loop receiver response.

A simple host model using the withdrawn driver and an RSSI that follows applied gain starts with a full-gain
reading of 260 for 20 polls (500 ms at the core's 25 ms period), then drops to 150. The loop has removed 79 dB
after the strong interval and needs 882 more polls (22.050 s) to return to at most 12 dB attenuation. The model
includes the loop's bounds and hold, and uses no hardware or foreign firmware. It demonstrates an undesirable
response to a signal step; it does not prove that this explains the reported crunchy/overloaded audio. The new
filter, AF control or hardware overload remain possible contributors.

## Verification and next physical check

Verify the generated tree against the patch series and its code against `b736e952`; build the target and check
its compiler/stack audits. Run receiver and radio-core regressions. Verify the public installer serves the stable
rollback image with the same checksum as its release.

Before recommending a new AM change, compare the same source, frequency, volume and antenna on the previous
and candidate versions. Record whether squelch 0 removes the cuts, the RF/noise and gain readings, and the audio
at controlled weak and strong levels. Change one receive component at a time. No aircraft-band RF is emitted
and no radio is flashed as part of this rollback task.

## Gain-only candidate (November 16)

The owner describes the current audio as saturated. The rollback still selects AM with `0x47 = 0x0740` and leaves
`0x13 = 0x037E` fixed. A strong signal therefore has no software gain reduction. This is a plausible source of
overload, not a measured diagnosis of the owner's audio. AF output clipping and front-end overload remain possible.

Patch `0046-am-bounded-receive-gain` changes only the receive gain control. It does not reinstate the withdrawn
filter, AF control, full-gain boost, `0x4A`, or noise-based squelch changes:

- Use the permissively licensed FD6818 gain table and target from RadioFoundry `ad79ab67` / `dc1140bf`.
- Start at the existing gain word and use it as a ceiling. On this board that is `0x037E`; never boost to `0x03FF`.
  If a gain word is unknown, preserve it and disable gain changes.
- Reduce gain to bring a strong reading to the target in one step. Discard the averaging history after every gain
  change: the next sample was measured at a different gain.
- After the hold, recover one table entry per status poll, without restarting the hold on each recovery step.
- Add back the attenuation at which each RSSI sample was taken, before updating the gain. Keep the existing AM
  RSSI offset and squelch mapping, so reducing gain does not itself mute the audio.
- Reset the gain on every AM tune and restore the previous word on leaving AM, including a direct change to DMR.
  Do not advance the loop while the receiver sleeps or transmits.

The host regression models a receiver whose RSSI follows the applied gain, including every input reading from
0 through 511, steady signals, the gain-table bounds, a strong-to-weak step, retuning, and leaving AM. At the
modeled strong reading 260, the gain reduction is 61 dB; after the source drops to 120, full original gain returns
in 55 status polls (1.375 s at 25 ms per poll). This is a software-model result, not a timing or audio measurement
on the radio. The withdrawn loop's stale-average double cut is a separate explicit regression.

The candidate requires the same physical comparison described above before promotion to a public stable release.
In particular, compare squelch 0 and 5 with the same station, antenna and volume, and check FM and DMR after AM.
No radio or RF bench is connected to this change's software validation.
