# Next session: sound (phase 7)

Where things stand: the game is on screen and plays (`12-video.md`). The
user played it at the end of session 5 (a new world, over two minutes in
the field, running and fighting): everything looked right. Sound is
silent, the most visible gap, so phase 7 comes before the rest of phase 6.

Today the 68000 is not run: the runtime answers SBL's sound driver at its
command blocks (sound RAM 0x700, cleared at the next poll) and publishes
the PCM play position from time (0x7A0 + 2 × stream, blocks of 4096
samples; `11-runtime.md`, `12-video.md`). The title's and the field's
music are sequences for the driver, not CD-DA (session 4).

## TODO

1. **The 68000**, an interpreter in saturnkit's runtime: SMPC SNDON/SNDOFF
   start and hold it, it runs the driver the game loads into sound RAM
   (`HYDLIDE/SOUND/` has two, `SDDRVS.TSK` and `SDDRVSO.TSK`: which
   program loads which), in slices at the master's polls, deterministic in
   virtual time. Its interrupts come from the SCSP. Whether to write it
   or take an existing core (Musashi: check its licence against MIT) is
   the first decision.
2. **The SCSP**: its registers at 0x25B00000, the 32 slots (PCM 8/16-bit,
   loops, the envelope, pitch, pan and level, FM), the timers A/B/C and
   the interrupts to the 68000 and to the SCU (sound request), the DSP
   (the areas load a DSP program), MIDI in/out if the driver uses them.
   Samples at 44 100 Hz, driven by virtual time.
3. **Out through SDL3**: an audio stream fed at the rate virtual time
   makes samples; with the window, paced by the host's clock like the
   video. Headless: a WAV of a run (`--wav`), for checking by ear and
   against Beetle.
4. **The handshake HLE retired**: with the driver running, the command
   blocks and the PCM play position are the driver's; keep the HLE as
   an option only if it helps tests stay fast.
5. **CD-DA**: the CD block's CD-DA plays (timed today) as samples, mixed
   through the SCSP's external input with the level the game sets; find
   where the 27 tracks play (open questions 6, 7, 14).
6. **Done when**: the movie's voice and music, the title's and the
   field's music and the field's effects are heard, in time with the
   picture, and sound like Beetle's.

## Later (the rest of phase 6)

* The same world in both (*Create world with code* HCTSPBMFCH in Beetle
  and in the port), compared view for view.
* VDP1 on the GPU at N× resolution, the software path as the reference.
* What the other areas ask of VDP1 and VDP2; the framebuffer's CPU view
  (open question 4); double-density interlace (question 3).

## When convenient

* Read the slave job (0x0602583C) and its master twin (0x060255DC), and
  the VDP1 command builder.
* 256 lines on a 60 Hz raster: check whether anything in the game depends
  on the PAL line count.
* Open questions 16 (the rest of the sound driver's area) and 17 (timer 1
  on every line: with the 68000 running, what OPEN's sound queue does).

## Useful

* Play: `python tools/run.py --play`. Headless to the field:
  `python tools/run.py` (8 s); pictures: `-- --shot N,...`
  (build/run/shot-N.png), video memory: `-- --dump N,...`.
* The oracle: `python tools/oracle.py --at 30:START,35.3:shot,...`
  (build/oracle/tSECONDS.png); Beetle runs at 50 frames a second, the
  times are wall-clock. RetroArch can also record its audio for the
  comparison.
* `--watch LO:HI` with `--trace` prints each access to the range with
  the caller's `pr` (canonical addresses: sound RAM is 05A00000).
* Regenerate, build and check everything: `python tools/recomp.py --build
  --test` (about 2.5 minutes).
* When a run stops or ends, the runtime prints where the master's last
  4096 polls were: what the game is waiting for.
