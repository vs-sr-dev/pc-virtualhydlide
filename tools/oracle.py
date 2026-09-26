"""Virtual Hydlide in Beetle Saturn (RetroArch), driven from here: the oracle
for what the port shows.

    python tools/oracle.py [--at SECONDS:WHAT,...] [--out DIR] [--quit SECONDS]

Boots the disc (iso/*.cue) in RetroArch's Beetle Saturn core and, at each
time given (seconds since the launch, the emulator running at its own
speed: 50 frames a second, the disc is European), does WHAT:

    shot                      a screenshot, saved as DIR/t<SECONDS>.png
    START / A+C / ...         press these buttons (Saturn names: UP DOWN LEFT
                              RIGHT START A B C X Y Z L R) for 0.15 s

RetroArch is driven over UDP: its command port (55355) takes SCREENSHOT and
QUIT, its network RetroPad (55400 for user 1) the buttons. The run leaves
RetroArch's own settings alone: an --appendconfig file in DIR gives it its
own save folder (emptied first, so every run starts from a Saturn with
nothing saved), its own core options (the user's, with no cartridge: with a
backup-RAM cartridge in, OPEN first asks which memory to save to, and the
port has none), the network RetroPad, and no saving of the configuration
on exit.

The times are wall-clock times, so two runs differ by a few frames.
"""
import argparse
import glob
import os
import shutil
import socket
import struct
import subprocess
import sys
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
RA_DIR = r"F:\RetroArch 2"
RETROARCH = os.path.join(RA_DIR, "retroarch.exe")
CORE = os.path.join(RA_DIR, "cores", "mednafen_saturn_libretro.dll")
USER_OPTS = os.path.join(RA_DIR, "config", "Beetle Saturn", "Beetle Saturn.opt")
CMD_PORT = 55355
REMOTE_PORT = 55400

# Beetle Saturn's pad on the RetroPad (libretro's joypad ids)
RETROPAD = {"B": 0, "Y": 1, "SELECT": 2, "START": 3, "UP": 4, "DOWN": 5, "LEFT": 6, "RIGHT": 7,
            "A": 8, "X": 9, "L": 10, "R": 11, "L2": 12, "R2": 13}
SATURN = {"UP": "UP", "DOWN": "DOWN", "LEFT": "LEFT", "RIGHT": "RIGHT", "START": "START",
          "A": "B", "B": "A", "C": "R", "X": "Y", "Y": "X", "Z": "L", "L": "L2", "R": "R2"}


def setup(out):
    saves = os.path.join(out, "saves")
    shots = os.path.join(out, "screenshots")
    for d in (saves, shots):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    opts = os.path.join(out, "beetle.opt")
    lines = []
    if os.path.exists(USER_OPTS):
        lines = [l.rstrip("\n") for l in open(USER_OPTS) if not l.startswith("beetle_saturn_cart")]
    with open(opts, "w") as f:
        f.write("\n".join(lines + ['beetle_saturn_cart = "None"']) + "\n")
    append = os.path.join(out, "append.cfg")
    with open(append, "w") as f:
        for k, v in (("savefile_directory", saves), ("savestate_directory", saves),
                     ("screenshot_directory", shots), ("core_options_path", opts),
                     ("game_specific_options", "false"), ("global_core_options", "true"),
                     ("config_save_on_exit", "false"), ("network_cmd_enable", "true"),
                     ("network_cmd_port", str(CMD_PORT)), ("network_remote_enable", "true"),
                     ("network_remote_enable_user_p1", "true"),
                     ("network_remote_base_port", str(REMOTE_PORT)),
                     ("pause_nonactive", "false"), ("savestate_thumbnail_enable", "false")):
            f.write('%s = "%s"\n' % (k, v))
    return append, shots


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--at", default="", help="SECONDS:WHAT,... (WHAT: shot, or buttons joined by +)")
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "oracle"))
    ap.add_argument("--quit", type=float, default=None, help="quit at this time (default: after the last event)")
    a = ap.parse_args()
    cue = glob.glob(os.path.join(ROOT, "iso", "*.cue"))
    if not cue:
        sys.exit("no .cue in iso/")
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    append, shots = setup(out)
    events = []
    for item in filter(None, a.at.split(",")):
        t, what = item.split(":", 1)
        events.append((float(t), what))
    events.sort()
    quit_at = a.quit if a.quit is not None else (events[-1][0] + 1 if events else 10)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def command(c):
        sock.sendto(c.encode(), ("127.0.0.1", CMD_PORT))
    def buttons(names, state):
        for n in names:
            if n not in SATURN:
                sys.exit("no Saturn button %s" % n)
            msg = struct.pack("<iiiiH2x", 0, 1, 0, RETROPAD[SATURN[n]], state)   # port, device (joypad), index, id, state
            sock.sendto(msg, ("127.0.0.1", REMOTE_PORT))

    log = os.path.join(out, "retroarch.log")
    p = subprocess.Popen([RETROARCH, "-L", CORE, cue[0], "--appendconfig=" + append, "-v", "--log-file=" + log])
    t0 = time.monotonic()
    releases = []
    shot_times = []
    try:
        pending = list(events)
        while True:
            now = time.monotonic() - t0
            for r in [r for r in releases if r[0] <= now]:
                buttons(r[1], 0)
                releases.remove(r)
            while pending and pending[0][0] <= now:
                t, what = pending.pop(0)
                if what == "shot":
                    command("SCREENSHOT")
                    shot_times.append(t)
                else:
                    names = what.split("+")
                    buttons(names, 1)
                    releases.append((now + 0.15, names))
            if now >= quit_at or p.poll() is not None:
                break
            time.sleep(0.005)
    finally:
        command("QUIT")
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    # the screenshots, oldest first, are the shots in order (RetroArch names them by the time of day)
    files = sorted(os.listdir(shots), key=lambda n: os.path.getmtime(os.path.join(shots, n)))
    for t, n in zip(shot_times, files):
        dst = os.path.join(out, "t%g.png" % t)
        shutil.move(os.path.join(shots, n), dst)
        print("%6.1f s: %s" % (t, dst))
    if len(files) != len(shot_times):
        print("%d screenshots asked for, %d came" % (len(shot_times), len(files)))


if __name__ == "__main__":
    main()
