# Sound

Phase 7: the Saturn's sound side in saturnkit's runtime. The game's own
sound driver runs on an emulated 68000 beside an emulated SCSP; what it
plays goes to the window's audio device, or to a WAV file.

```sh
python tools/run.py --play                           # the window, with sound
python tools/run.py -- --wav build/run/run.wav       # headless, the run's sound as a WAV
python tools/oracle.py --at 20:START --record        # Beetle Saturn's, as build/oracle/record.wav
```

## What is heard

The run to the field (`tools/run.py`, 120 s of game time), second by
second, next to Beetle Saturn's recording of the same screens:

| Game time | Screen | Sound |
|---|---|---|
| 1.3 s | OPEN starts the driver (SNDOFF, `SOUND/SDDRVSO.TSK` into sound RAM, SNDON) | the 68000 boots at 0x1000, stack 0xA000 |
| 3.5–20 s | The opening movie | its PCM stream, two slots (0 right, 1 left) at 22 050 Hz, and the driver's effects over it |
| 20–30 s | The title | nothing: silent in Beetle too |
| 30 s | START | the confirmation |
| 38–59 s | STARTUP's menus (STARTUP and M_CHI load `SOUND/SDDRVS.TSK`) | the menu music (a sequence), the cursor and confirm effects |
| 60–71 s | Creating and loading the world | nothing |
| 71 s on | The field, M_CHI | the field's music, the effects of walking and fighting |

**Against Beetle** (`tools/oracle.py --record`, the movie, not skipped):
the two recordings, aligned by cross-correlation, correlate at 0.99 over
the movie in both channels, with the same stereo image, at a constant
offset (no drift beyond a few samples of RetroArch's resampling over
12 s). The port is 1.20 times louder (+1.6 dB), the same ratio in every
band from 20 Hz to 9 kHz, so a plain gain: the digital path is the same
as Mednafen's (level 7 is 0 dB, each step −6 dB; MVOL 15 is 0 dB; the
movie's slots use DISDL 6, TL 0), and where Beetle loses 1.6 dB is not
found. The user's ears: see `00-sessions.md`.

## How it is built

`saturnkit/runtime`:

| File | What |
|---|---|
| `sound.cpp` | The 68000 (Musashi), its bus, SNDON/SNDOFF, the pace; the SH-2's view of sound RAM and the SCSP; the WAV file |
| `scsp.cpp` | The SCSP: 32 slots, envelopes, LFOs, FM, timers, interrupts, DMA, the DSP, the mix |
| `third_party/musashi` | Musashi 4.60 (MIT), configured as a plain 68000 |
| `host.cpp` | The SDL3 audio stream |
| `cdblock.cpp` | CD-DA sectors as samples for the SCSP's external input |

### Time

The machine's time (virtual, `11-runtime.md`) drives the sound side too:
at each of the master's polls, `sound_tick` makes every sample due by
then at 44 100 Hz, and before each sample the 68000 runs 256 cycles
(11.29 MHz, as on the Saturn). A run is still the same run every time.
The SH-2 and the 68000 meet at the poll's grain, about 100 µs, through
sound RAM, which is all the driver's handshake asks.

In a window, VBlank-IN waits for the host's clock (`12-video.md`), so the
samples come at the device's rate on average; the stream starts 50 ms
ahead, drops a chunk that would take it past 250 ms and pads with 50 ms
of silence when it runs dry. The stop report says how often each
happened: in a 25-second run, once (at the start) and never.

The cost: the run to the field takes 13 s on the host instead of 8.

### The 68000

Musashi, reset at SNDON with the stack pointer and PC from sound RAM 0
and 4 (the driver's header: SSP 0xA000, PC 0x1000), held at SNDOFF. Its
bus: sound RAM at 0x000000 (512 KB, mirrored to 0x0FFFFF), the SCSP's
registers at 0x100000. Its interrupts are the SCSP's, autovectored, at
the level SCILV0–2 give the highest bit pending and enabled.

### The SCSP

Registers as 16-bit words, byte writes merged. Per sample:

* **Timers A, B, C**: count up every 2^TxCTL samples from the value
  written (loaded at the next count), and set their bit (6, 7, 8) for
  both CPUs on reaching 0xFF; bit 10 is set every sample.
* **Slots**: 8- or 16-bit PCM from sound RAM, or noise, at 44.1 kHz ×
  2^OCT × (1 + FNS/1024), linearly interpolated; no loop, loop, reverse,
  alternating; FM from the sound stack (MDL, MDXSL, MDYSL); the envelope
  (attack, two decays, release, key-rate scaling, EGHOLD, LPSLNK); pitch
  and level LFOs. Key on and off at KYONEX, for every slot whose KYONB
  changed.
* **Out**: each slot, attenuated by TL, to the direct mix (DISDL, DIPAN),
  to the DSP's input MIXS[ISEL] (IMXL) and to the sound stack; the DSP's
  EFREG 0–15 mixed by slots 0–15's EFSDL and EFPAN, the external input
  EXTS 0–1 (CD audio) by slots 16–17's; MVOL.
* **The DSP**: the 128-step program, its TEMP, MEMS, COEF, MADRS, the
  ring buffer in sound RAM (RBP, RBL) with its floating-point format.
  M_CHI's program is 64 steps, MIXS in and EFREG 2–3 out, its
  ring buffer at RBP 6, 32 K words.
* **The slot monitor** (0x408): CA, SGC and EG of the slot MSLC names. CA
  is what the driver publishes as the PCM play position that paces the
  movie (session 5's finding): with the driver running, the runtime no
  longer publishes it.
* **DMA** between sound RAM and the registers, done at once.

The envelope times, the key-rate scaling, the LFO tables, the FM scale and
the DSP step follow MAME's `scsp.cpp` and `scspdsp.cpp` (BSD-3-Clause,
credited in the file); the timers follow the hardware as Mednafen
documents it.

### CD audio

A CD-DA play (`cdblock.cpp`) reads its sectors at 75 a second as before;
each sector's 588 stereo samples (little-endian, as on the disc image)
queue for the SCSP, which takes one at each of its samples into EXTS 0–1.
In the field slots 16 and 17 have EFSDL 0 and M_CHI's DSP program does
not read EXTS (it reads MIXS 0–3 and 8–14 and writes EFREG 2–3),
so the CD would be silent there; the driver presumably sets the
CD's level when a game asks for CD audio. **Not yet heard**: no CD-DA
play comes up from the boot to the field (open questions 6, 7, 14).

## What changed from session 5

The handshake HLE is gone: the command blocks at 0x700 are cleared by
the driver, the PCM play position at 0x7A0 is the driver's, from the
SCSP's CA. The movie still runs at its 15 frames a second, and the
recording matches Beetle's at a constant offset, so it is paced as there.

## Limits

* **Not done**: MIDI (its input reads empty), the DSP's ring-buffer
  accesses on even steps (MAME's rule), the SCSP's own timing of slot
  and DSP steps within a sample.
* **Level**: 1.6 dB above Beetle's, above.
* The envelope is MAME's model (linear attack, decays in 3/32 dB steps
  from time tables), not a cycle model of the chip's.
