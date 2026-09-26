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
