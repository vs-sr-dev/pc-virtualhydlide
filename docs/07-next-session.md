# Next session: the code map (phase 2)

1. **Function discovery** for stripped SHC code, in saturnkit: seeds from
   crt0, `bsr` targets, `mov.l` literals at prologues, interrupt handlers
   installed through the BIOS, the slave job; walk the code with delay
   slots; `mova` + `mov.w @(r0,rn)` + `braf` switch tables sized from the
   compare before them. Check: every branch lands inside a known function;
   no function crosses another.
2. **An executable map** (`saturnkit.exe`): the programs, their crt0,
   text/data/BSS, the program-swap set (which images share an address).
3. **Match the engine across programs** by function bytes with literals
   masked, so a name given in M_CHI carries to the other 12 programs.
4. **Read the frame loop** in M_CHI: from `main` (0x0600B068) to the
   limiter call at 0x06036508; what `n` is and where it comes from; what
   the limiter's result feeds (open questions 1 and 2).
5. **Read HYDSYS's service table** (0x060EE004): the CD, sound and
   program-swap services (open question 5).
6. **A Python SH-2 interpreter** in saturnkit, enough to run isolated
   functions (the division helper 0x0603E918, fixed-point routines) as the
   recompiler's future oracle.
7. **Oracle set-up**: Beetle Saturn through RetroArch for screenshots; see
   whether a debugger (Mednafen standalone) is available for run-time
   values.
8. Listen to `build/audio/track02.wav` (the user) — open question 7.
