# Next session: the recompiler (phase 3)

1. **`saturnkit.recomp` emitter**: one C++ function per discovered entry,
   over a context (r0–r15, SR as T/S/Q/M/IMASK, GBR, VBR, MACH/MACL, PR);
   delay slots emitted before the jump with the target and condition
   taken first; `bsr`/`jsr` as calls, `rts` as return; branches to other
   entries as tail calls; switch tables as C++ switches; a computed jump
   left unresolved falls back to a dispatch over the function's own
   labels. Exact `div1`, `mac.w`/`mac.l` with S, `addc`/`subc`/`negc`,
   `tas.b`.
2. **Per-program modules**: the 15 programs compiled into one binary,
   each in its own namespace; a dispatcher keyed by the program occupying
   0x0600B000 (identified by a checksum of its first bytes when `exec`
   loads it), HYDSYS and LOADER at their own addresses.
3. **Guest memory model** for the generated code: WRAM-L/WRAM-H as host
   arrays, big-endian accesses, the cache-through mirror, everything else
   as MMIO callbacks (the runtime of phase 4 fills them in).
4. **Self-test**: the four division helpers, the bit-field helper and a
   few fixed-point routines run recompiled and in `sh2emu` on the same
   random inputs; results equal.
5. Build with CMake + Ninja + clang (MSYS2), as wiikit.
6. Still from phase 2, when convenient: the slave job (0x0602583C) and the
   VDP1 command builder; the oracle set-up (Beetle via RetroArch).
7. The user: listen to `build/audio/track02.wav` (open question 7).
