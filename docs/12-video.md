# VDP1 and VDP2 on screen

Phase 5: the game in a window, drawn by saturnkit's VDP1 and VDP2 in
software, played with the keyboard or a gamepad.

```sh
python tools/run.py --play                    # the window
python tools/run.py -- --shot 600,1300,7200   # headless, pictures in build/run/shot-N.png
python tools/oracle.py --at 30:START,35.3:shot  # Beetle Saturn, driven from here (below)
```

Keys: arrows, Enter START, Z X C = A B C, A S D = X Y Z, Q W = L R; a
gamepad's d-pad or left stick, Start, south A, east B, right shoulder C,
west X, north Y, left shoulder Z, triggers L and R. F12 saves the
picture, F11 or Alt+Enter switches fullscreen.

## What is on screen

Every screen from the boot to the first field, next to Beetle Saturn's:

| Screen | Program | What draws it | Against the oracle |
|---|---|---|---|
| The opening movie | OPEN, 320×224 | VDP1 alone (BGON 0): one normal sprite a frame, 16-bit RGB, inside the user clip | the same frames; 15 fps, as the audio clock paces it (below) |
| The title | OPEN, 320×224 | NBG0 as a 512×256 RGB bitmap, and 16 sprites (4 bpp, lookup table) | the same picture |
| The menus, "Now creating a new world" | STARTUP, 320×256 | NBG2 (cells 8×8, 256 colours, 2-word names) and some 80 sprites, flipped ones among them; polygons, user clipping | the same layout, boxes, text and background |
| The field | M_CHI, 320×256 | NBG1 (the sky: cells 16×16, 256 colours) and three VDP1 draws a frame, below | the same elements and look; not the same view (below) |

A frame in the field is three command lists, drawn one after the other:
two polygons that clear the framebuffer (the upper half to colour 0, so
the sky shows through, the lower half to grey), then some 210 distorted
sprites (the world: 4 bpp through a lookup table, most with Gouraud
shading, a shadow in 8 bpp), then the HUD (36 normal sprites, 4 distorted
ones, lines and polygons, two of them Gouraud-shaded). The framebuffer is
never erased by VDP1 (FBCR is always 3, manual change).

**The sky is stretched for PAL.** NBG1's vertical coordinate increment is
0xDF/256 = 0.871: VDP2 spreads 223 lines of the sky over the 256 lines of
the European screen. A 224-line design, converted.

**The field is not the same view.** "Create world randomly" makes a
different world in each run (the code shown on the creation screen:
HCTSPBMFCH in the port's run, QPPCKRRLGB in the oracle's), so the two
first fields are different places. Comparing a view pixel for pixel
means creating the same world by its code in both.

**Not the game's**: the SEGA licence screen Beetle shows before the movie
is the BIOS's, drawn from IP.BIN; the HLE boot goes straight to the 1st
read file. And with a backup-RAM cartridge in (Beetle's automatic
choice), OPEN first shows its *Backup Memory Utility*, asking where to
save; the port has no cartridge, so the oracle runs without one too.

## How it is built

`saturnkit/runtime`: `vdp1.cpp`, `vdp2.cpp`, `host.cpp`, and `video.cpp`
for the raster and the bus; `video.h` between them.

**VDP1** draws when the game starts a draw (PTMR 1, or 2 at a frame
change), the whole command table at once, into the framebuffer being
drawn. Every shape is a quadrilateral drawn the chip's way: its left edge
A→D and right edge B→C walked in the same number of steps, a line
between them at each step, Bresenham lines with an extra pixel where both
coordinates step (VDP1's anti-aliasing, which leaves no holes). The
texture's row is the step's, its column the position along the line.
Colour modes, transparent pixels, end codes, system and user clipping,
mesh, MSB on, replace, shadow, half-luminance, half-transparency and
Gouraud are there; 8-bit framebuffers and rotation are not (a run that
asks for them stops). In the field that is about 780 000 pixel writes a
frame (overdraw and the anti-aliasing pixels), a few milliseconds: the
headless run to the field takes 8 s instead of 3.

**VDP2** composes a field at VBlank-IN, when a window or a picture file
wants it: NBG0–NBG3 in cell mode, NBG0/NBG1 as bitmaps too, fractional
scroll and coordinate increments, every sprite type, palette and RGB
mixed, priorities with the chip's order for ties, colour calculation of
the top two layers, colour offsets, the back screen. Rotation planes,
line and cell scroll, mosaic, windows, the line colour screen, special
priority and colour calculation, shadows on VDP2's layers and high
resolutions are not done; a register that asks for one is noted once.
None came up from the boot to the field.

**The window** (SDL3, OpenGL 4.5) shows each composed field on a 4:3
screen. For a disc whose only area is Europe (IP.BIN's area symbols: `E`)
the screen is 256 lines tall and a 224-line picture sits in the middle of
it with a border above and below, as on a European TV and in the oracle.
Time stays virtual: each VBlank-IN waits for the host's clock, so the
game runs at the Saturn's speed and a run with the same presses is the
same run.

**The pad** is the host's keyboard and gamepad, or'ed with the
`--input` script, in the SMPC's INTBACK answer.

## What the screens needed

* **The frame changes at the end of VBlank.** The movie player asks for
  a frame change (FBCR 3) in its VBlank-IN handler once a draw has ended,
  and gets it in the same blanking (Mednafen changes frame at VBlank-OUT).
  Changed at VBlank-IN, the request waited a field and the two
  framebuffers took turns: a new frame, then the one before it.
* **The PCM play position is in blocks of 4096 samples.** The movie
  player's PCM task (0x06055C36) reads one byte a stream at 0x7A0 + 2 ×
  stream and counts each change of it; the stream code turns the count
  into samples with a shift by 12 (0x060560C8). Session 4's runtime
  published the position a sample at a time: the byte changed at every
  look, the player refilled the audio ring 2.5 times too fast, and the
  movie ran 2.4 times too fast in bursts (three frames a VBlank apart,
  then a pause). Now the ring fills at 22 050 samples a second and the
  movie shows a new frame every 4 VBlanks, sometimes 3 or 5.

## The oracle

`tools/oracle.py` starts Beetle Saturn in RetroArch (`F:\RetroArch 2`)
and drives it over UDP: RetroArch's command port takes `SCREENSHOT` and
`QUIT`, its network RetroPad (user 1) the buttons, at times given in
seconds since the launch (wall-clock: two runs differ by a few frames).
It leaves RetroArch's settings alone: an `--appendconfig` file gives the
run its own empty save folder, the user's Beetle options without a
cartridge, the network RetroPad, and no saving of the configuration.
Beetle runs the disc as a European Saturn, 50 frames a second.
