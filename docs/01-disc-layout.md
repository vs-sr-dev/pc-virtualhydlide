# The disc

European release, Redump-style set: one .cue, 28 .bin files, one per
track. Everything below comes from `python -m saturnkit.disc CUE --info`
and `--list`.

## IP.BIN (system area, sectors 0–15 of track 1)

| Field | Value |
|---|---|
| Hardware id | `SEGA SEGASATURN` |
| Maker | `SEGA ENTERPRISES` |
| Product | `MK-81380`, version `V1.000`, date `19950630` |
| Device | `CD-1/1` (one disc) |
| Areas | `E` (Europe) — one area code block, "For EUROPE.", at 0x0E04 |
| Peripherals | `J` (control pad) |
| Title | `VIRTUAL HYDLIDE` |
| IP size | 0x8000 |
| Stacks | master 0, slave 0 (BIOS defaults) |
| 1st read | loaded at **0x0600B000**, whole file |

The 1st read file is `A.BIN` (341 528 bytes), byte-identical to
`HYDLIDE/EXEC/OPEN.BIN`: the boot program is the opening program under a
second name.

The ISO 9660 volume has no volume, system, publisher or preparer id; the
creation date is 1995-06-29 20:43:03. Its volume size, 160 511 sectors,
covers the whole disc, audio included.

## Tracks

Track 1 is data (MODE1/2352, 52 018 sectors, 101.6 MB of image); tracks
2–28 are CD-DA. Every audio track has a 2-second pregap (150 frames; 149
for track 2).

| Track | Length | Track | Length | Track | Length |
|---|---|---|---|---|---|
| 02 | 0:05 | 11 | 1:32 | 20 | 0:08 |
| 03 | 1:30 | 12 | 1:05 | 21 | 0:14 |
| 04 | 0:47 | 13 | 1:10 | 22 | 0:04 |
| 05 | 3:01 | 14 | 0:57 | 23 | 0:04.4 |
| 06 | 0:48 | 15 | 0:10 | 24 | 0:04 |
| 07 | 0:55 | 16 | 0:54 | 25 | 1:01 |
| 08 | 1:03 | 17 | 0:54 | 26 | 0:55 |
| 09 | 1:08 | 18 | 1:22 | 27 | 0:43 |
| 10 | 1:11 | 19 | 1:13 | 28 | 0:14 |

The root directory also lists the audio tracks as files `CDDA1`–`CDDA27`
(ISO 9660 records pointing at the audio LBAs), Sega's mastering
convention. 25 minutes of CD audio across 27 tracks suggest the music is
mostly CD-DA; what the 290–400 KB sound-RAM image each area loads holds
(effects only, or sequences too) is still open (`05-open-questions.md`).

## File tree

458 files. Everything the game uses sits under `HYDLIDE/`:

| Directory | Files | Size | Contents |
|---|---|---|---|
| `EXEC` | 16 | 3.4 MB | the programs: one per area plus opening, startup, menu, ending; `HYDSYS.BIN` and `LOADER.BIN`; a copy of IP.BIN |
| `MAP01`–`MAP09` | 5–10 each | 5.8 MB | per-area terrain and dungeon data: `.MDL` models, `.SPR` sprite banks, `.BG` backgrounds, `.MAP`, `.OUT`, `.DAT` |
| `CHARA` | 34 | 3.7 MB | monsters and NPCs as `.GOB` animation banks (BAT, BEE, DRAGON, KOBOLD, ROPER, VARALYS, ZOMBIE…) |
| `P0`–`P3` | 69 each | 46 MB | the player character, four sets of 69 `.GOB` banks (`HYDLIDE/P%d/P_%d%d%X.GOB`) |
| `GAMEDATA` | 2 | 43 KB | `GAMEGRPH.GOB`/`.SPR`, loaded by every area program |
| `GRAPH` | 11 | 2.9 MB | still screens: SEGA logo (`SEGA.BIN`, 143 360 bytes = 320×224 in 15-bit RGB), opening, score, rank, continue, ending |
| `MENU` | 9 | 128 KB | fonts, window and item sprites, name entry |
| `SOUND` | 21 | 5.1 MB | the sound driver (`SDDRVS.TSK`, `SDDRVSO.TSK`), sound-RAM images per area, tables |
| `CPKDATA` | 2 | 33 MB | the two movies, `OPEN_E.CPK` and `ENDING.CPK` |

## Programs, areas and their data

Each area is a separate program. The strings each one contains tie it to
its data:

| Program | Area data | Sound bank(s) | Monsters (`CHARA/*.GOB`) |
|---|---|---|---|
| `OPEN.BIN` (= `A.BIN`) | — | DEMO | — ; plays `OPEN_E.CPK` |
| `STARTUP.BIN` | — | all area banks listed | — |
| `MENU.BIN` | — | — | — |
| `M_CHI.BIN` | MAP01 (the field) | CHIJO | BEE, FAIRY0–2, JELLY, JELLY_B, KOBOLD, PAL, TREEMONS |
| `M_DRA.BIN` | MAP02 | KYUKETSU, KYUKET_B | BAT, BOMBD2, VAMPIRE1, ZOMBIE |
| `M_SYA.BIN` | MAP03 | SHAKU, SHAKU_B | DRAGON, DGON_BDY, GOLD_AM, LADY_AM |
| `M_KYU.BIN` | MAP04 | KYUDEN, KYUDEN_B | EEL, FAIRY0–2, MIMIC, ROPER, SKELETON |
| `M_FIN.BIN` | MAP05 | TORIDE, VARALYS | BAT, SKELETON, VAMPIRE2, VARALYS, WIZARD |
| `M_ORDEAL.BIN` | MAP06 | SHIREN | KOBOLD2, WILL |
| `M_RUINS.BIN` | MAP07 | HAIKYO | HROPER, KOBOLD, TRAP02–42, ZOMBIE |
| `M_SEAL.BIN` | MAP08 | FUIN, FUIN_B, KYUKET_B | BLACK_AM, GOLD_AM, MIMIC, TRAP, WIZARD, ZOMBIE |
| `M_BURIAL.BIN` | MAP09 | BOCHI | ZOMBIE |
| `ENDING.BIN` | — | — | — ; plays `ENDING.CPK` |

The sound banks carry the Japanese name of the area the program carries in
English: CHIJO (地上, the surface), KYUDEN (宮殿, palace), SHIREN (試練,
ordeal), HAIKYO (廃墟, ruins), FUIN (封印, seal), BOCHI (墓地, graveyard),
KYUKETSU (吸血, vampire), TORIDE (砦, fortress).
