# Next session: the recompiler (phase 3)

Where things stand: every program is mapped (`saturnkit.recomp.discover`),
the engine is matched across programs (`saturnkit.recomp.match`), and an
SH-2 interpreter (`saturnkit.sh2emu`) can run isolated functions. Phase 3
turns the discovered functions into C++ that compiles, links and computes
what the interpreter computes.

## TODO

1. **The emitter**, `saturnkit/recomp/emit.py`, one C++ function per
   discovered entry:
   * context: r0–r15, SR split into T/S/Q/M/IMASK, GBR, VBR, MACH/MACL, PR;
   * delayed branches: take the target and the condition first (`bt/s`
     reads T before the slot; `jsr @rn` reads rn before the slot), emit
     the slot, then jump;
   * `bsr`/`jsr` with a known target as direct C++ calls, `rts` as
     return, a branch to another entry as a tail call; `jsr` through a
     register as a dispatch lookup;
   * switch tables (the three forms `discover` resolves) as C++ `switch`;
     a computed jump left unresolved falls back to a switch over all of the
     function's own labels;
   * exact semantics as in `sh2emu`: `div0s/div0u/div1`, `mac.w`/`mac.l`
     with the S bit, `addc/subc/negc/addv/subv`, `rotcl/rotcr`, `tas.b`,
     `dmuls/dmulu`, `mul.l`, `muls/mulu.w`;
   * interrupt safe points at loop back-edges and calls (a hook the runtime
     fills later); `sleep` as an idle point.
2. **Per-program modules.** The 15 programs in one binary, each in its
   own namespace (`m_chi::f_0602A566`…); a dispatch table per program; the
   active program chosen by what `exec` (0x060EE08C) loaded at 0x0600B000,
   recognised by a checksum of the loaded image. HYDSYS (0x060EE000) and
   LOADER (0x060C0000) always present.
3. **Guest memory for the generated code**: WRAM-L (0x00200000) and WRAM-H
   (0x06000000) as host arrays, big-endian loads and stores, the
   cache-through mirror (0x2xxxxxxx) folded, purge writes (0x4xxxxxxx)
   ignored, everything else routed to MMIO callbacks that phase 4 fills.
4. **Self-test**, a small executable: the four division helpers
   (`__divlu` 0x060224DC, `__modlu` 0x0603CAE0, `__divls` 0x0603E980,
   `__modls` 0x0603EA34), the bit-field helper (0x0603E918) and a few
   fixed-point routines, recompiled, against `sh2emu` on the same random
   inputs. Done when they agree on every input.
5. **Build**: CMake + Ninja + clang from MSYS2
   (`PATH=/c/msys64/mingw64/bin`), C++20, as wiikit; the generated project
   in `build/recomp`, the build in `build/recomp-build`.
6. **Done when**: all 15 programs' functions compile and link; the
   self-test passes; the count of unresolved jumps and unknown targets is
   written in `docs/09-recompiler.md`.

## When convenient

* Read the slave job (0x0602583C) and its master twin (0x060255DC), and
  the VDP1 command builder: phase 5 will need them.
* The oracle: a scripted Beetle Saturn run through RetroArch
  (`F:\RetroArch 2`, as `D:\Homebrew6\SAT-LBA\run.ps1` does) for reference
  screenshots of the SEGA logo, the title and the field.
* Group 0x03 of HYDSYS's system call (0x060EEF6C): the CD-audio commands,
  and when track 2 (the thank-you) is played.

## Useful

* Ghidra's own function list for a program, to compare with `discover`:
  `saturnkit/ghidra/ExportFuncs.java` (the recipe is in its header; JDK 21
  at `J:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot`).
* Names for other programs:
  `python -m saturnkit.recomp.match build/extract/HYDLIDE/EXEC/M_CHI.BIN@0600B000 build/extract/HYDLIDE/EXEC/<P>.BIN@0600B000 --names tools/names-m_chi.tsv --out build/names/<P>.tsv`
