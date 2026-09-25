# Next session: the runtime core (phase 4)

Where things stand: every program is C++ that computes what the SH-2
computes (`09-recompiler.md`), with a runtime that has the work RAMs, the
dispatch over modules and nothing else: any hardware access stops the
self-test. Phase 4 gives that code a Saturn to run on, up to the first
frame, without drawing anything yet.

## TODO

1. **Boot, HLE**, in saturnkit's runtime (`boot`): read IP.BIN, load the
   1st read file (A.BIN) at 0x0600B000, leave the state as the BIOS does
   (stack, SR, VBR, the BIOS work area), identify and activate its module,
   call its entry.
2. **The BIOS services** (`bios`): the pointers the game uses (0x0600026C
   and 0x06000300–0x06000358, `saturnkit.hw.BIOS`) filled with addresses
   the recompiled code cannot reach (the BIOS ROM),
   which `sh2_call_unknown` maps to host functions: `SYS_SETUINT`/
   `GETUINT`, `SETSINT`/`GETSINT`, the SCU mask (`SETSCUIM`, `CHGSCUIM`,
   `GETSCUIM`), the semaphores (`TASSEM`, `CLRSEM`), the clock
   (`GETSYSCK`, `CHGSYSCK`), BUP (a host file), and 0x0600026C.
3. **The program swap**: `exec` (0x060EE08C) loads a program and jumps
   through 0x0600026C without returning. The runtime identifies the new
   image (`sh2_identify`), activates it, and unwinds the host stack to its
   own loop before calling the new program's entry: the old program's C++
   frames must not stay underneath.
4. **Interrupts** (`scu`): the SCU's mask and status registers, VBlank-IN
   and VBlank-OUT from the host clock at 60 Hz (TVSTAT says NTSC), timers
   0 and 1, sprite-draw end; delivered at the safe points (`sh2_poll`):
   SR and PC pushed on the guest stack, the handler called through the
   table SYS_SETUINT filled, its `rte` back to the sentinel.
5. **SMPC** (`smpc`): COMREG, SR, SF, IREG, OREG; INTBACK with a pad (no
   input yet), SSHON/SSHOFF, SNDON/SNDOFF, CDON/CDOFF.
6. **The slave SH-2**: a second context; a write to SINIT (0x21000000)
   runs the job at 0x060503D4 to its end (deterministic first).
7. **The CD block** (`cdblock`), at its registers (HIRQ, CR1–CR4, the data
   port): the commands GFS and HYDSYS's file group use, over the extracted
   tree. CD-DA play commands recorded, not played.
8. **SCU DMA** (direct and indirect, levels 0–2) and, as plain memory for
   now, VDP1 and VDP2 registers and VRAM, CRAM, the SCSP's sound RAM: what
   is written is kept, reads return it.
9. **Done when**: A.BIN runs through its initialisation to its frame loop
   (VBlanks counted, VDP1 frame changes requested), HYDSYS is loaded and
   `exec` swaps to the next program; a log of every hardware register
   touched and every call to a non-entry (open question 15), with counts,
   in `docs/11-runtime.md`.

## When convenient

* Read the slave job (0x0602583C) and its master twin (0x060255DC), and
  the VDP1 command builder: phase 5 will need them.
* The oracle: a scripted Beetle Saturn run through RetroArch
  (`F:\RetroArch 2`, as `D:\Homebrew6\SAT-LBA\run.ps1` does) for reference
  screenshots of the SEGA logo, the title and the field.
* Group 0x03 of HYDSYS's system call (0x060EEF6C): the CD-audio commands,
  and when track 2 (the thank-you) is played.

## Useful

* Regenerate, build and check everything: `python tools/recomp.py --build
  --test` (about 2 minutes; `--no-vectors` skips the interpreter).
* The generated code is readable: each line carries its address and
  instruction, `build/recomp/p_<program>_NNN.cpp`.
* Ghidra's own function list for a program, to compare with `discover`:
  `saturnkit/ghidra/ExportFuncs.java` (the recipe is in its header; JDK 21
  at `J:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot`).
* Names for other programs:
  `python -m saturnkit.recomp.match build/extract/HYDLIDE/EXEC/M_CHI.BIN@0600B000 build/extract/HYDLIDE/EXEC/<P>.BIN@0600B000 --names tools/names-m_chi.tsv --out build/names/<P>.tsv`
