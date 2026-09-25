# The recompiler

Phase 3: every function of the 15 programs, translated to C++ that
compiles, links, and computes what the SH-2 computes. The code lives in
saturnkit (`recomp/emit.py`, `recomp/__main__.py`, `recomp/selftest.py`,
`runtime/`); this repository gives it the list of programs
(`tools/recomp.py`).

```sh
python tools/recomp.py --build --test     # generate, vectors, build, self-test (about 2 minutes)
```

writes the C++ into `build/recomp`, builds `build/recomp-build` (CMake,
Ninja, clang 22 from MSYS2, C++20, `-O3`), and replays the self-test.

## What the generated code looks like

One C++ function per discovered entry, `void f_XXXXXXXX(SH2Context& c)`,
in one namespace per program (`p_m_chi`, `p_hydsys`…). The frame limiter,
as generated:

```cpp
void f_0602A566(SH2Context& c) {
    c.r[6] = 0x06057F40u;  // 0602A566 mov.l 0x0602A578,r6
L_0602A568:
    c.r[2] = ld32(c.r[6]);  // 0602A568 mov.l @r6,r2
    c.r[3] = ld32(c.r[4]);  // 0602A56A mov.l @r4,r3
    c.r[2] -= c.r[3];  // 0602A56C sub r3,r2
    c.t = c.r[5] > c.r[2];  // 0602A56E cmp/hi r2,r5
    if (c.t) { SH2_POLL(c); goto L_0602A568; }  // 0602A570 bt 0x0602A568
    c.r[3] = ld32(c.r[6]);  // 0602A572 mov.l @r6,r3
    { const uint32_t x = c.pr; st32(c.r[4], c.r[3]); c.pc = x; return; }  // 0602A574 rts ; mov.l r3,@r4
}
```

* **Registers** in `SH2Context`: r0–r15, SR as separate T, S, Q, M and
  the interrupt mask, GBR, VBR, MACH, MACL, PR.
* **Delayed branches** read what they need first (`bt/s` reads T,
  `jsr @rn` reads rn, `rts` reads PR, `rte` pops PC and SR), run the slot,
  then go. A branch into a delay slot runs it as an instruction of its own.
* **Calls**: `bsr` and `jsr` set PR and call the C++ function; after the
  call, `SH2_RET` checks that the callee's `rts` came back to the return
  address. A branch to another entry is a tail call.
* **Calls and jumps through registers** compare the register with the
  target analysis found and otherwise go to `sh2_call`, which looks the
  address up in the active modules: a wrong guess costs a lookup, never a
  wrong call. Computed jumps (`jmp`, `braf`) become a `switch` over their
  targets (switch tables, literals, constants); an unresolved one gets
  every instruction of its own function as a case before `sh2_call`.
* **Literal loads** (`mov.l @(disp,PC)`) become constants: the image is
  identified by its crc32 before its code runs, so the pool is known. A
  pool slot that some literal points at would be read from memory
  instead; there are none in this game.
* **Safe points** (`SH2_POLL`) at loop back-edges, before calls and after
  `ldc …,sr`: a countdown the runtime uses for interrupts and time.
  `sleep` and `trapa` call the runtime.
* **Memory**: WRAM-L and WRAM-H as host arrays holding big-endian bytes,
  inline at their cached and cache-through addresses; everything else
  goes to `sh2_io_read/write` (WRAM-H's mirrors, the purge area, and the
  hardware, which phase 4 fills).
* **Semantics**: `saturnkit/sh2emu.py`'s, instruction for instruction:
  `div0s/div0u/div1`, `mac.w` and `mac.l` with the S bit, the carry and
  overflow forms, `rotcl/rotcr`, `tas.b`, the multiplies.

## Programs as modules

Each program is a module: its image's base, size and crc32, and its
entries sorted by address. The runtime keeps one active module per address
range; `sh2_identify(0x0600B000)` finds which of the 13 swapped programs
is in memory by its crc32, and `sh2_activate` puts it in place. HYDSYS
(0x060EE000) and LOADER (0x060C0000) sit in their own ranges. OPEN.BIN
stands for A.BIN, its identical twin.

## The counts

`build/recomp/report.txt`, calls and jumps through a register by how the
target was found:

| Program | Functions | Instructions | switch | literal | constant | pointer | unresolved calls | unresolved jumps |
|---|---|---|---|---|---|---|---|---|
| HYDSYS | 421 | 24 824 | 7 | 588 | 51 | 30 | 13 | 7 |
| LOADER | 336 | 16 184 | 1 | 409 | 28 | 28 | 13 | 7 |
| OPEN | 1 253 | 141 845 | 14 | 5 001 | 1 277 | 94 | 184 | 11 |
| STARTUP | 663 | 129 429 | 11 | 5 321 | 1 189 | 204 | 698 | 0 |
| MENU | 233 | 26 040 | 5 | 547 | 90 | 45 | 114 | 0 |
| M_CHI | 695 | 116 438 | 13 | 4 181 | 1 054 | 189 | 243 | 0 |
| M_DRA | 663 | 110 787 | 12 | 3 923 | 973 | 185 | 236 | 0 |
| M_SYA | 654 | 112 766 | 12 | 3 928 | 968 | 183 | 237 | 0 |
| M_KYU | 691 | 116 719 | 12 | 4 142 | 998 | 200 | 231 | 0 |
| M_FIN | 674 | 116 539 | 13 | 4 150 | 989 | 187 | 255 | 0 |
| M_BURIAL | 664 | 109 162 | 12 | 3 823 | 996 | 184 | 231 | 0 |
| M_ORDEAL | 663 | 113 811 | 11 | 3 890 | 969 | 186 | 232 | 0 |
| M_RUINS | 678 | 114 609 | 12 | 3 913 | 978 | 183 | 230 | 0 |
| M_SEAL | 714 | 124 444 | 12 | 4 210 | 1 050 | 203 | 239 | 0 |
| ENDING | 1 254 | 141 454 | 14 | 4 970 | 1 240 | 94 | 186 | 11 |
| **Total** | **10 256** | **1 515 051** | | | | | **3 342** | **36** |

(Instructions count code shared between functions once per function.
Sites are counted the same way.)

* **Unresolved jumps: 36**, none in the ten area programs. All are tail
  calls through tables of function pointers indexed at run time
  (`mov.l @(r0,rT),r0` or `@(disp,r0)`, then `jmp @r0`): two tables each
  in HYDSYS (0x060FA480, 0x060FA4B8), LOADER (0x060C81C4, 0x060C81FC),
  OPEN (0x06059E70, 0x06059EA0) and ENDING (0x06059878, 0x060598A8), and
  in OPEN and ENDING four more through an object's own table (offsets
  0x164–0x170 from the pointer in r14). `sh2_call` dispatches them.
* **Unresolved calls: 3 342**: `jsr` through a register loaded from a
  structure (callbacks, per-object handlers). They are dispatched at run
  time; STARTUP has the most.
* **Calls through pointers** (the "pointer" column): the BIOS service
  vectors (0x06000300…) and HYDSYS's system call (the pointer at
  0x060EE004), resolved at run time.
* **Unknown targets: 0.** No static call or jump target, in any program,
  is outside the entries of its own module or of a module that can be
  loaded beside it.
* **Volatile literals: 0.** Every literal load is folded to a constant.

The build: 1.5 million lines of C++ in 202 files (93 MB), compiled from
scratch in 76–85 s on 16 threads; `librecomp.a` 58 MB.

## The self-test

Two halves, both replayed by the build's `selftest` executable against
vectors recorded with the interpreter (`sh2emu`): the full register state
before and after each call, and the crc32 of both work RAMs after each
function.

| Vectors | Functions | Vectors | Failures |
|---|---|---|---|
| saturnkit's instruction test | 775 | 9 300 | 0 |
| the 15 programs | 2 647 | 42 148 | 0 |
| **Total** | **3 422** | **51 448** | **0** |

**The instruction test** is saturnkit's own: a synthetic program with each
of the 126 instruction forms (of the 142 the decoder knows) that do not
branch, sleep, trap or load PR, three register choices each (the same
register twice, r0, random), alone and in the delay slot of an `rts`;
random registers, SR bits, operands and memory. Then the control flow: `bt`/`bf`, `bt/s`/`bf/s` with a slot that
changes T, a branch into its own slot, loops on `dt` with back-edges,
`bsr`, `jsr` with rn overwritten in the slot, `bsrf`, a tail `jmp`, an SHC
switch through `braf`, `rts` whose slot reloads PR, 32 `div1` steps after
`div0u` and after `div0s`, `mac.w` in a row.

**The game's functions**: in each program, every function that on random
registers returns while writing nothing but its stack, and, failing that,
every function that does the same with r4–r7 pointing into random data
(and writes only there): arithmetic, fixed-point and table helpers, and
the routines on vectors, matrices and structures. HYDSYS is resident, as
in the game. In M_CHI: 132 + 53 functions, and the four division helpers
and the bit-field helper by name.

What it covers: every instruction form, and the game's own leaf and
near-leaf code. The vectors run 5.7% of M_CHI's instructions (203
functions, 68 distinct operations) and 10.6% of HYDSYS's. The rest (the
frame loop, the renderer, anything that touches hardware) is checked when
the game runs, in phase 4.

### What it caught

* **A function starting at the wrong place.** When discovery follows code
  below a function's entry (a tail shared with a function found later),
  the C++ function began at the lowest address. It now opens with a
  `goto` to the entry. 14 functions in M_CHI, 28 in OPEN had it.
* **A branch into a delay slot** stopped discovery at the slot (already
  seen as code), so the code after it was never reached. Fixed in
  discovery; the game's code does not do this, the test does.
* **A data pointer taken for a function.** `main` reads the BSS end
  through a pointer to the last word of crt0's literal pool (0x0600B064);
  its bytes decode cleanly into `main`, so discovery made it a function
  (7 programs, and one more in M_FIN that it led to). A literal that the
  code dereferences where it loads it is now data.
* **The shift ladder with an offset**, the one computed jump discovery did
  not resolve (session 2): `add #-24` on the index before the table read.
  Now a fourth switch form; every program but HYDSYS and LOADER has one.

## Known limits

* The semantics are the interpreter's. Where the interpreter could differ
  from the hardware (`mac.w` saturation with S set, `div1` corner cases),
  both agree and both can be wrong; the game's own run is the check.
* The program swap: `exec` jumps to the new program through the BIOS
  pointer at 0x0600026C and never returns. In C++ that is a call that
  does not come back; the runtime has to unwind to its main loop (phase 4).
* Interrupts are delivered at safe points only. Code that waits on a
  hardware flag without a back-edge in between cannot be interrupted; the
  loops in the game all have one.
* No cycle counts: time comes from the host clock and the safe-point
  countdown, not from instructions (enough for a game capped by VBlanks).
