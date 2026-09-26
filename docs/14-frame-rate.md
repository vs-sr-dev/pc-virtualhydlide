# The frame rate

Level 3 of the plan (`06-attack-plan.md`): lower the frame cap, the 5 of
`limiter(&last, 5)` in `main`, and let the game draw 30 or 60 frames a
second, trusting its logic to step by elapsed VBlanks.

```sh
python tools/run.py --play --frame-interval 1     # 60 fps
python tools/run.py --play --frame-interval 2     # 30 fps
python tools/run.py --play                        # 12 fps, as shipped
```

## How the cap is changed

The recompiler hooks the instruction (session 6, saturnkit's `recomp
--hook`): after `mov #5,r5` at 0x0600B6F4 in the nine area programs (the
same bytes, 0xE505, in all nine; `tools/recomp.py` names them), the
generated code calls `sh2_hook`, and the runtime's `--hook
0600B6F4:r5=N` makes r5 N there. `tools/run.py --frame-interval N` passes
it. The game is otherwise untouched; without the option nothing changes.

The cap works: at interval 1 the field draws 60 frames a second (2 930
frames in 49 s of game time instead of 587), at 2 thirty.

## What does not follow elapsed time

The same walk (the run to the field, then UP held from VBlank 7300 to
7600) at each interval, the player's position read from memory (the
player's object is at 0x06058D6C, its position at +0x0C; the field's
view of it at 0x0604F2C0):

| Interval | Frames in the walk | Distance along the walk's axis |
|---|---|---|
| 5 (12 fps) | 60 | 28.0 |
| 2 (30 fps) | 150 | 68.5 |
| 1 (60 fps) | 300 | 85.5 |

Frame by frame the step is the same at every interval: 0.5 units a
frame (0x8000 in 16.16), whatever dt was. The clocks do follow elapsed
time (the play time on screen is the same at the same VBlank at every
interval), but **the player's motion is stepped per frame**: in the
world update (0x0602EFDC, the function that computes and clamps dt),
the player's motion comes from a script of 4-byte entries (0x0605F164,
picked by its state) that the update reads one entry a frame
(+0x48 the pointer, +0x56 the entries left), and the entry's speed goes
to the collision-checked move (0x0602DFFC) as that frame's velocity.
The walk's pace is the script's, one entry a frame, as long as the
frames are 5 VBlanks apart.

So lowering the constant alone makes the player (and possibly
whatever else is stepped by such scripts, the animation poses among
them) run 2.5 or 5 times too fast at 30 or 60 fps. Level 3 needs the
script's step made to follow dt as well: advance an entry every 5
VBlanks of accumulated dt and move by velocity × dt / 5 each frame, in
every place that steps an object this way. Where those places are, and
how many, is the next thing to find.

## The census (session 6)

`--watch` now covers the work RAMs: every store in the range, its value,
the VBlank and the recompiled function that made it (`--watch-vblanks`
narrows it). The field's object array, standing still for two seconds
(VBlanks 7300–7420) at intervals 5 and 1, compared field by field
(`build/census.py`, not kept: the table is the result). The array is at
0x06058D6C, 100 bytes an object: object 0 is the player, 1–8 what moves
around it.

| Fields | What they look like | At interval 1 | Written by |
|---|---|---|---|
| +0x48, +0x50, +0x54, +0x56, +0x62 | the motion script: entry pointer, a phase falling by 256 a frame, counters | 5 times as many steps | 0x0602EFDC (player), 0x0602D3FE (the others) |
| +0x0C, +0x10, +0x14 | position | 3 to 10 times as far | the move (0x0602DFFC, copy 0x060225B8), 0x0602D116 |
| +0x24, +0x2C, +0x3C, +0x44 | orientation (a rotation's cosines and sines) | 3 to 12 times as much turning | 0x06023744 |
| +0x5C | a speed or distance | up to 100 times | 0x0602D116 |

Outside the array, two structures move 5 to 11 times too fast as well
(0x06059A10 and 0x06059A1C, written by 0x06031144 and 0x060319FE;
0x06059C80-0x06059C88, copied every frame), perhaps the camera.

Nothing in the array follows dt. And the per-frame steps are not a few
lines: 0x0602D3FE is a state machine of about a thousand instructions
where each state counts frames in its own way (+0x56 incremented and
compared with 4 in one state, decremented to 0 in another, +0x62 and
+0x52 elsewhere), with some twenty places that touch the counters.
Making all of it follow dt means rewriting each state's timing, for the
player, the other objects and the camera, in every area program.

## The way taken: the fields in between, drawn by the runtime

With the user (session 6) the frame rate is reached the other way: the
game keeps its 12 frames a second and its own logic, untouched, and the
runtime draws the four fields between two of its frames.

```sh
python tools/run.py --play --interp
```

**What the runtime does** (saturnkit's `vdp1.cpp`, `--interp`). Every
frame the game draws (the draws between two frame changes) is recorded:
each command VDP1 executes, its 32 bytes, the clipping and local
coordinates each draw starts from, VDP2's scroll registers and a copy of
VDP1 RAM at the frame change. At every field until the next change the
last frame is drawn again into a framebuffer of the runtime's own, each
command's vertices moved from where its counterpart was in the frame
before by the part of the interval gone by, and VDP2's NBG scroll moved
the same way; that framebuffer is the field's sprite layer. The picture
is one game frame behind (83 ms at 12 fps) and moves at 60 fields a
second. A command with no counterpart is drawn where it is.

**Which command is which** (the game layer, `tools/game/hydlide.cpp`).
The field's 3D list is some 220–250 commands a frame, most of them ground
tiles that share a handful of textures, so matching by look and nearness
confuses them. The layer gives each command a key from the game's own
drawing calls, through recompiler hooks: the instance being drawn (r4 of
0x06025384, which 0x0601E5E4 calls once per instance; the master draws it
or hands a copy to the slave, whose job starts at 0x060255DC), the model
part (r5 of the five drawers 0x06026084, 0x060269B4, 0x06026FB8,
0x060275D4, 0x06027D88), the drawer's call site, the command's number
within the part and the part's occurrence in the frame. Every command
passes through 0x06024DD0, which copies it into a slot of a double
buffer that 0x06024EB8 sends whole to VDP1 RAM at 0, so the slot is the
command's address: the keys go to VDP1 with the send. In a turn in the
field, with keys: no key twice in a frame, 80 % of the commands matched
(the rest come into view), a median move of 34 pixels a frame.

**Two findings on the way.** The player is not a model: it is one
distorted sprite (and a shadow) whose picture the game renders anew
every frame into VDP1 RAM (0x776C0 onward, sent with the frame). And the
next frame's textures arrive a field before its frame change, so a frame
drawn again from live VDP1 RAM in the interval's last field showed the
new player picture in the old one's place, as stripes: hence the copy of
VDP1 RAM at each change.

Checked: the movie, the title and the menus are the same picture with and
without `--interp`, pixel for pixel; twelve fields of a turn in the field
move evenly, with no stray polygons. It costs about 1.4 ms of host time
a field.

**After the user's first play** (two glitches reported: the ground
sometimes split by pure white lines and wedges, and trees garbled by
direction and distance, righting themselves up close):

* *Trees.* Only a handful of instances pass through 0x06025384; the map
  is drawn by the slave, one job per block of the map in view (the copy
  at 0x060555B0: the block's world position at +0/+4/+8 on a grid of
  0x200000, its quarter turn at +12, its model at +28). Blocks of one kind
  share their model, trees included, so the key's "occurrence of the
  part" swapped one tree for another whenever a block left the view. A
  block is now known by its position.
* *White.* The lower half of the screen is cleared to a near-white grey
  (0xF39C) before the ground is drawn, and it shows wherever two ground
  shapes stop meeting. A shape with no counterpart (just come into view)
  used to stay where it was while its neighbours moved; now it moves with
  what it touches: a matched vertex it shares, a matched edge it lies on
  (near the camera the finer ground meets the coarser in T-junctions),
  else the nearest matched vertex; in two passes, so that new ground
  meets new ground too. Matched shapes that share a vertex move it by the
  mean of their moves.

Measured on 500 fields of turning and walking: fields with more than 20
near-white pixels on the ground, 5 with `--interp` as without it (pale
stones), down from 40; one small wedge at a screen corner remains in two
or three fields. Trees stay whole through a turn.

Still to do: the other area programs (the layer's addresses are
M_CHI's); zero latency, by drawing the fields toward the frame the game
has already built when it waits in its limiter (its list is complete
there; its textures come later, with the send).
