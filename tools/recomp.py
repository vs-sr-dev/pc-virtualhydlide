"""Recompile Virtual Hydlide's programs to C++ and check them.

    python tools/recomp.py [--build] [--test] [--no-vectors]

1. `python -m saturnkit.recomp`: the 14 distinct programs (A.BIN is
   OPEN.BIN) as modules, and saturnkit's instruction test, into
   build/recomp; report.txt there has the counts per module.
2. `python -m saturnkit.recomp.selftest`, one process per program: the
   vectors of every function that runs alone (on its stack, or on what its
   pointer arguments point at), with HYDSYS resident as in the game, into
   build/recomp/selftest.
3. --build: CMake, Ninja and clang from MSYS2 into build/recomp-build.
4. --test: the self-test executable on every vectors file.

Run from the repository root, after the disc has been extracted
(build/extract).
"""
import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
EXEC = os.path.join(ROOT, "build", "extract", "HYDLIDE", "EXEC")
OUT = os.path.join(ROOT, "build", "recomp")
BUILD = os.path.join(ROOT, "build", "recomp-build")
MSYS = r"C:\msys64\mingw64\bin"

# name, load address (docs/03-executables.md)
RESIDENT = [("HYDSYS", 0x060EE000), ("LOADER", 0x060C0000)]
SWAPPED = ["OPEN", "STARTUP", "MENU", "M_CHI", "M_DRA", "M_SYA", "M_KYU", "M_FIN",
           "M_BURIAL", "M_ORDEAL", "M_RUINS", "M_SEAL", "ENDING"]
PROGRAMS = RESIDENT + [(n, 0x0600B000) for n in SWAPPED]
# hooks (saturnkit.recomp --hook): after `mov #5,r5` at 0x0600B6F4 in the nine
# area programs, the frame cap main's loop hands the limiter
# (docs/03-executables.md); tools/run.py --frame-interval sets it
AREAS = ["M_CHI", "M_DRA", "M_SYA", "M_KYU", "M_FIN", "M_BURIAL", "M_ORDEAL", "M_RUINS", "M_SEAL"]
FRAME_CAP = 0x0600B6F4
HOOKS = {n: [FRAME_CAP] for n in AREAS}
# the game layer's (tools/game/hydlide.cpp): M_CHI's instance draw, the slave's job, the 3D drawers, the command
# emitter and the send to VDP1, for --interp
HOOKS["M_CHI"] += [0x06025384, 0x060255DC, 0x06026084, 0x060269B4, 0x06026FB8, 0x060275D4, 0x06027D88, 0x06024DD0, 0x06024EB8]
GAME = os.path.join(ROOT, "tools", "game", "game.cmake")
# the self-test's division and bit-field helpers, by name (tools/names-m_chi.tsv)
M_CHI_FUNCS = "060224DC,0603CAE0,0603E980,0603EA34,0603E918"


def spec(name, base):
    return "%s=%s@%08X" % (name, os.path.join(EXEC, name + ".BIN"), base)


def vectors(name, base):
    from saturnkit.recomp import selftest
    images = [spec(name, base)] if base != 0x0600B000 else [spec("HYDSYS", 0x060EE000), spec(name, base)]
    names = os.path.join(ROOT, "tools", "names-m_chi.tsv") if name == "M_CHI" else \
        os.path.join(ROOT, "build", "names", name + ".tsv")
    argv = ["--out", os.path.join(OUT, "selftest", name.lower() + ".txt"), "--test", name, "--auto"]
    for i in images:
        argv += ["--image", i]
    if os.path.exists(names):
        argv += ["--names", names]
    if name == "M_CHI":
        argv += ["--funcs", M_CHI_FUNCS]
    selftest.main(argv)
    return name


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--no-vectors", action="store_true")
    a = ap.parse_args()
    from saturnkit.recomp.__main__ import generate, parse_spec
    t0 = time.time()
    generate([parse_spec(spec(n, b)) for n, b in PROGRAMS], OUT, optest=True, hooks=HOOKS)
    if not a.no_vectors:
        os.makedirs(os.path.join(OUT, "selftest"), exist_ok=True)
        with concurrent.futures.ProcessPoolExecutor() as ex:
            list(ex.map(vectors, *zip(*PROGRAMS)))
    print("generated in %.0f s" % (time.time() - t0))
    env = dict(os.environ, PATH=MSYS + os.pathsep + os.environ["PATH"])
    if a.build:
        t = time.time()
        tool = lambda x: shutil.which(x, path=env["PATH"])      # CreateProcess searches the parent's PATH
        subprocess.run([tool("cmake"), "-S", OUT, "-B", BUILD, "-G", "Ninja", "-DCMAKE_CXX_COMPILER=clang++",
                        "-DCMAKE_C_COMPILER=clang",
                        "-DSATURNKIT_EXTRA=" + GAME.replace(os.sep, "/")],
                       env=env, check=True, stdout=subprocess.DEVNULL)
        subprocess.run([tool("ninja"), "-C", BUILD], env=env, check=True)
        print("built in %.0f s" % (time.time() - t))
    if a.test:
        files = [os.path.join(OUT, "selftest", "optest.txt")] + \
                [os.path.join(OUT, "selftest", n.lower() + ".txt") for n, _ in PROGRAMS]
        r = subprocess.run([os.path.join(BUILD, "selftest.exe")] + [f for f in files if os.path.exists(f)], env=env)
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
