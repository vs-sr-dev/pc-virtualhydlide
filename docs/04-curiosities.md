# Curiosities

Things found on the way that the port does not need.

1. **The boot program has two names.** The 1st read file `A.BIN` is
   byte-identical to `HYDLIDE/EXEC/OPEN.BIN`: the opening program, stored
   twice, once where the BIOS wants it and once with its siblings.

2. **A stray IP.BIN.** `HYDLIDE/EXEC/IP.BIN` (3 872 bytes) is the first
   3 872 bytes of the disc's system area, copied into the file system.

3. **The default ranking.** `A.BIN` holds a ranking of ten entries, 100 000
   points down by 10 000, each with a name and the monster that ended the
   run: NAITO (Varalys), NISHI (Mad Dragon), AOP (Evil Mage), YUMI (Eel),
   OGAWA (Skeleton), SHIMA (Gold Armor), NORI (Roper), KIRI (Zombie), KEN
   (Kobold), TOYO (Jelly). NAITO at the top, beaten by the final boss, is
   presumably Tokihiro Naitō, who created Hydlide; the others look like
   staff nicknames.

4. **"Hi! Come come everybody. … Guu… I'm sleepinggguuu…"** Two strings
   just before the ranking in `A.BIN`, next to `STAT`, `ERR `, `FILM`.
   Where they are shown is not known yet.

5. **Two languages of area names.** The programs are named in English
   (`M_ORDEAL`, `M_RUINS`, `M_SEAL`, `M_BURIAL`), the sound banks of the
   same areas in Japanese (`SHIREN`, `HAIKYO`, `FUIN`, `BOCHI`).

6. **The Japanese font is still on the disc.** `MENU/HYDFNT.BIN` (49 KB,
   indexed by Shift-JIS codes) sits next to the European programs' own
   `HYDFNTE.BIN` (8 KB).

7. **A file that is not there.** `OPEN.BIN` loads `STNHYD.MAP` but its
   error message says `Load Error:HYDMAP2.MAP`: the file was renamed and
   the message was not.

8. **Linked in four minutes.** `M_CHI.BIN` says `Version Jun 26 1995
   (17:13:07)`, `OPEN.BIN` `(17:17:04)`: the programs were built one after
   another, four days before the date in IP.BIN (1995-06-30).

9. **Debug traps left in.** The programs install their own CPU exception
   handlers that print `CPU TRAP:CPU Address Error [%08X]` and `CPU TRAP:
   DMA Address Error`, and fill the stack with 0xAA at boot to see how
   deep it goes.

10. **A loader nobody calls.** `LOADER.BIN` (at 0x060C0000, with the full
    list of programs) is referenced by no other program.

11. **The save file's name**: `TE_HYD_1DAT` follows the ranking in
    `A.BIN`, presumably the backup-memory file name.

12. **Track 2 says thank you.** The first audio track, five seconds long,
    is music with a voice saying "Thanks for playing, T&E Soft": a
    sign-off, where many discs put a warning not to play the data track.
    When the game plays it is not known yet.
