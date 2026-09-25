# The game's files: a first look

The port does not need to understand the data: the game's own code reads
it, and the port recompiles that code. These notes are for reading the
code and for later improvements (asset dumps, higher-quality textures).
Nothing here is decoded yet beyond the headers.

## T&E's chunked format

Most files are sequences of chunks, each a 4-character tag and a 32-bit
big-endian size, in the manner of IFF:

| Tag | Seen in | Notes |
|---|---|---|
| `OANI` | `CHARA/*.GOB`, `P*/*.GOB` | animation records, several per file; sprite frames follow |
| `VER ` | `*.MDL` | followed by the text `T&E 3D Model Data` |
| `MODL`, `VTX `, … | `*.MDL` | the code's own tag list reads `GOUR MODL OBJ TBL VECT VER VTX`: Gouraud tables, models, objects, vertices |
| `SCB `, `CLUT` | `*.SPR` | sprite control blocks and colour tables (15-bit RGB colours, MSB set) for VDP1 |
| `BG  `, `CLUT` | `*.BG` | backgrounds, with a 256-colour table |
| `GOBJ` | `*.OUT` | dungeon object placement? |

The code reports `MDL data format error!` and `DECODE_PDAT: DECODE BUFF
OVER!`, so at least some data is compressed (`PDAT`).

## Movies — `CPKDATA/*.CPK`

Sega FILM, version 1.04: `FILM` header, `FDSC` (Cinepak, `cvid`, 320×224,
24-bit; audio at 22 050 Hz), `STAB` sample table. A standard format that
FFmpeg reads; in the port the game's own Cinepak player (Sega's CPK
library, in the programs) will decode them, fed by the emulated CD.

## Sound — `SOUND/`

* `SDDRVS.TSK`, `SDDRVSO.TSK` — the 68000 sound driver, most likely
  Sega's standard one. Both start with a 68000 vector table (initial stack
  0x0000A000, reset PC 0x00001000), so they load at sound-RAM address 0.
  `OPEN.BIN` names both; `HYDSYS.BIN` only `SDDRVS.TSK`.
* `STNHYD.MAP` — the sound area map (where each bank sits in sound RAM).
* `AREATBL.BIN`, `SNDTBL.BIN` — tables the programs load first.
* `CHIJO.BIN`, `KYUDEN.BIN`… — one sound-RAM image per area, 290–400 KB;
  each begins with a small directory whose first entry (`0x0000B000`,
  `0x00000540`) names `dsp1.EXB`, an SCSP DSP effect program.
* `SETTEI.BIN` (設定, settings), `DEMO.BIN`.

## Screens — `GRAPH/`

`SEGA.BIN` is a raw 320×224 15-bit RGB bitmap (every word has its MSB
set, VDP1/VDP2 "RGB" pixels). The 82 432-byte screens (`SCORE`, `RANK`,
`CONTINUE`, `STARTUP`, `HI_SCORE`, `COMPLETE`) and the larger `OPENING*`
and `ENDING*` files are not identified yet.

## Fonts — `MENU/`

`HYDFNT.BIN` (49 KB) starts with a table of Shift-JIS codes (`8140 8149
8194…`): the Japanese font kept on the European disc. `HYDFNTE.BIN` (8 KB)
is the one the European programs load (`HYDLIDE/MENU/HYDFNTE.BIN`).
