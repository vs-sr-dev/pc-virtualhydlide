// Virtual Hydlide's game layer: what this port adds to saturnkit's runtime,
// built into the saturn executable (game.cmake, through tools/recomp.py). It
// works through recompiler hooks (saturnkit's recomp --hook, the addresses
// in tools/recomp.py's HOOKS) and does nothing unless an option asks for it.
//
// --interp: the fields between the game's frames are drawn by vdp1.cpp,
// each command moved part of the way from its counterpart in the frame
// before. For the field's 3D list this layer says which command is which,
// so that the many tiles and trees of the same texture are not confused
// (docs/14-frame-rate.md). The key of a command is the instance drawn, the
// model part, the drawer and its call site, the command's number within the
// part, and how many times that part of that instance was drawn before in
// the frame:
//
//   * the instance: 0x0601E5E4 draws a few instances (the player, the
//     sprites around it) through 0x06025384, r4 the instance's structure at
//     a fixed address; the map is drawn by the slave, a job (0x060255DC) for
//     each block of the map in view, known by the block's position;
//   * the part: the five drawers (0x06026084, 0x060269B4, 0x06026FB8,
//     0x060275D4, 0x06027D88) are called with r5 the part, in the model's
//     data;
//   * every 3D command goes through 0x06024DD0 (r4 the 32-byte command, r5
//     its depth), which copies it into the slot the write pointer
//     0x060551B8 names in one of two buffers (their bases at 0x060551B0,
//     the index at 0x060551AC): at its entry the slot gets the key;
//   * 0x06024EB8 sends the buffer to VDP1 RAM at 0 (a DMA of the whole
//     buffer, so slot n is the command at 32 * n) and starts the draw: at
//     its entry the keys go to vdp1_next_draw_keys.
//
// These are M_CHI's addresses (the first field); the other area programs
// share the engine at other addresses, to be matched when they are played.
#include "saturn.h"
#include "video.h"
#include <map>
#include <tuple>
#include <unordered_map>
#include <vector>

namespace {

constexpr uint32_t kInstance = 0x06025384, kSlaveJob = 0x060255DC, kEmit = 0x06024DD0, kSend = 0x06024EB8;
constexpr uint32_t kDrawers[] = {0x06026084, 0x060269B4, 0x06026FB8, 0x060275D4, 0x06027D88};
constexpr uint32_t kWritePtr = 0x060551B8, kIndex = 0x060551AC, kBases = 0x060551B0;

struct Part { uint32_t part, drawer, seen, n; };
uint32_t g_instance[2];                                 // per CPU
Part g_part[2];
std::map<std::tuple<uint32_t, uint32_t, uint32_t>, uint32_t> g_seen;   // (instance, part, drawer): times this frame
std::unordered_map<uint32_t, std::vector<uint64_t>> g_keys;       // buffer base -> key by slot

uint64_t mix(uint64_t h, uint64_t v) { return h ^ (v + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2)); }
uint32_t canon(uint32_t a) { return a & 0xDFFFFFFFu; }   // without the cache-through bit
uint32_t buffer_base() { return canon(ld32(kBases + 4 * (ld32(kIndex) & 1))); }

void on_instance(SH2Context& c, uint32_t) {
    if (g_cfg.interp) g_instance[c.cpu & 1] = canon(c.r[4]);
}

// The slave's jobs are the map's blocks: r4 is the copy at 0x060555B0, the
// block's world position at +0, +4, +8 (a grid of 0x200000), its turn at
// +12, its model at +28. Blocks of one kind share their model and parts,
// so the block is known by where it is.
void on_slave_job(SH2Context& c, uint32_t) {
    if (!g_cfg.interp || c.cpu != 1) return;
    uint32_t a = canon(c.r[4]);
    g_instance[1] = (uint32_t)mix(mix(mix(mix(ld32(a), ld32(a + 4)), ld32(a + 8)), ld32(a + 12)), ld32(a + 28));
}

void on_drawer(SH2Context& c, uint32_t addr) {
    if (!g_cfg.interp) return;
    int cpu = c.cpu & 1;
    uint32_t part = canon(c.r[5]);
    g_part[cpu] = {part, addr, g_seen[{g_instance[cpu], part, addr}]++, 0};
}

void on_emit(SH2Context& c, uint32_t) {
    if (!g_cfg.interp) return;
    uint32_t base = buffer_base(), ptr = canon(ld32(kWritePtr));
    if (ptr < base || ptr - base >= 0x10000) return;
    uint32_t slot = (ptr - base) / 32;
    int cpu = c.cpu & 1;
    Part& p = g_part[cpu];
    uint64_t key = mix(mix(mix(mix(mix(mix(1, g_instance[cpu]), p.part), p.drawer), p.seen), c.pr), p.n++);
    std::vector<uint64_t>& keys = g_keys[base];
    if (keys.size() <= slot) keys.resize(slot + 1);
    keys[slot] = key;
}

void on_send(SH2Context&, uint32_t) {
    if (!g_cfg.interp) return;
    uint32_t base = buffer_base(), ptr = canon(ld32(kWritePtr));
    std::vector<uint64_t> keys = g_keys[base];
    keys.resize(ptr > base ? (ptr - base) / 32 : 0);
    vdp1_next_draw_keys(std::move(keys));
    g_seen.clear();
}

struct Register {
    Register() {
        sh2_hook_add(kInstance, on_instance);
        sh2_hook_add(kSlaveJob, on_slave_job);
        for (uint32_t d : kDrawers) sh2_hook_add(d, on_drawer);
        sh2_hook_add(kEmit, on_emit);
        sh2_hook_add(kSend, on_send);
    }
} g_register;

}   // namespace
