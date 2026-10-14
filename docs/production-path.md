# D-RTI production path — the ESP32-S3 / C5 route

Companion to the baseline in [`baseline.md`](baseline.md).

**Status: not built.** This document is the *engineering* path from the simulation baseline to a
physical node mesh, and the specific fixes for the four failure modes that appear once you stop
paying the commodity-phone tax. Nothing here has been validated on hardware; the hardware claims
are per Espressif's own documentation (see References).

---

## Why the constraint changes

The baseline's whole cost was the OS sandbox: no monitor mode, no raw CSI, so links had to be
probed as sequential pairwise unicast, and a sweep cost `N(N-1)` exchanges. A dedicated MCU
removes that constraint at the source:

- hardware **CSI** per frame — `esp_wifi_set_csi()`;
- **promiscuous** receive, so a node hears frames not addressed to it;
- **raw frame TX** — `esp_wifi_80211_tx` — so a node can send a broadcast at a fixed rate.

That converts a sweep from `N(N-1)` unicast exchanges into `N` broadcast slots. Everything
below is what that exposes.

## 1. Broadcast probing

One broadcast frame is received by all `N-1` other nodes at once; each records its own link from
that single transmission. A sweep is `N` broadcast slots, not `N(N-1)` exchanges — airtime goes
`O(N^2)` → `O(N)`.

One consequence worth stating explicitly: a sweep yields `N(N-1)` link measurements for
`N(N-1)/2` unique links, so **every link is measured twice — once per direction.**

## 2. Failure mode: broadcast frames are not ACKed

Unacknowledged broadcast means link dropouts. Do not solve this with retries — solve it with
redundancy and inference:

1. **Directional redundancy.** Because each link is measured from both ends (§1), a single lost
   frame usually still leaves the other direction. Amplitude is reciprocal; keep whichever
   direction arrives, or fuse both with a per-direction offset calibrated on an empty room.
2. **Temporal gap-filling, not retransmits.** `dy` for a given link is smooth in time — at
   1.4 m/s a walker moves ~1.4 cm in 10 ms — so a per-link temporal filter (EMA / Kalman) or
   low-rank matrix completion reconstructs missing rows without a single ACK.
3. **Robust inversion.** Drop missing rows from `(W, dy)` and weight the survivors; use a
   Huber/Tukey loss so one corrupt row cannot drag the solve.
4. **Over-provision.** At `N = 50` there are 1,225 links and ~2,450 measurements per sweep — a
   lossy sweep is still heavily over-determined.

## 3. Failure mode: CSI phase is not coherent packet-to-packet

Stock ESP32 has no per-packet phase reference, so each frame's CSI carries an arbitrary common
phase rotation (CFO/SFO). Three answers, in order of effort:

1. **Default — don't use phase.** The forward model is attenuation-based (`dy`), so amplitude RTI
   is immune. Use the **full per-subcarrier amplitude vector**, not a scalar RSSI: that is
   `M >> L` measurements per link, for free (frequency diversity).
2. **Relative phase within a packet** — SpotFi-style linear sanitisation: fit and remove the
   linear-in-subcarrier slope (SFO) and offset (CFO) from the unwrapped phase. Usable for
   intra-packet processing (AoA-style); not absolute range.
3. **True coherence** — round-trip (two-way) phase between a pair cancels the local-oscillator
   offset; or share a clock, which §4 makes cheap.

## 4. Failure mode: TDMA sync and drift

1. **You may not need TDMA at all.** Slot alignment exists only to avoid collisions. Measurement
   *identity* comes from the frame header (source MAC + seq) and microsecond RX timestamps
   (`esp_timer`). So strict TDMA can be replaced with **collision-tolerant CSMA broadcast +
   random backoff**: a collision just drops a link, which §2 absorbs. Sync then matters only for
   *timestamping* (the tracking stage), not for measurement.
2. **If you want deterministic slots, use a wire.** The nodes are stationary and mains/USB
   powered — run one shared trigger/PPS line to every node. Sub-millisecond alignment, no drift,
   and it hands you the shared clock that §3(3) wants. Cheapest fix in the design.
3. **Wireless fallback.** A leader beacon plus FTSP-style offset/drift estimation (linear fit over
   the last `M` beacons). Sub-millisecond over short sync intervals; ESP32 timers are microsecond
   resolution.

## 5. Failure mode: interference and contention

1. **Channel choice.** Scan and park on the quietest of 1 / 6 / 11; if 2.4 GHz is crowded, use a
   dual-band part — **ESP32-C5 (2.4 + 5 GHz Wi-Fi 6)** — and move to 5 GHz.
2. **Fixed legacy rate (1–6 Mbps).** Longer preamble/payload gives more CSI samples and a more
   robust link.
3. **Frequency diversity.** Measure a link on more than one channel; interference is
   frequency-selective, so the polluted channel can be rejected — and multi-band `dy` enriches
   the inversion for free.
4. **Dodge the beacons.** APs beacon roughly every 102.4 ms; schedule broadcasts into the gaps.
5. **Your own collisions dominate** in a dense mesh — handled by §4. External APs are handled by
   1 and 3.

## 6. The interlocking view

| Limit | Primary fix | Cost |
|---|---|---|
| Dropped broadcast links | bidirectional redundancy + temporal gap-fill + robust inverse | firmware + a little math |
| Phase incoherence | amplitude-only by default; sanitise or share a clock if needed | none by default |
| TDMA sync + drift | drop TDMA (CSMA broadcast) or wire a sync line | 2 wires, or nothing |
| Interference | 5 GHz / quiet channel / multi-channel / beacon gaps | channel planning |

The three cheap moves compound: a **wired sync line** fixes drift and phase together, and
**broadcast + backoff + gap-filling** removes the need for precise scheduling at all.

## 7. Architecture sketch

```
N × ESP32-S3 (or C5)      one shared sync line (optional)
        │                        │
        └── 2.4/5 GHz broadcast ─┤
        │                        │
        └── CSI over UDP/serial ──► host aggregator (Pi / laptop)
                                     └─ W, Tikhonov inversion, tracker
```

The MCUs only transmit broadcasts and dump CSI; all inversion stays on the host, where the
existing `drti` code already lives.

---

## References

- `espressif/esp-csi` — official Wi-Fi CSI firmware (`esp_wifi_set_csi()`).
- Espressif ESP-IDF — `esp_wifi_80211_tx` (raw frame TX), promiscuous mode.
- ESP32-C5 datasheet — 2.4 + 5 GHz dual-band Wi-Fi 6.
- Wilson & Patwari, *Radio Tomographic Imaging with Wireless Networks* (2010) — forward model.
- Kotaru et al., *SpotFi* (SIGCOMM 2015) — CSI phase sanitisation.
- Maróti et al., *FTSP* (2004) — flooding time synchronisation.
