#!/usr/bin/env python3
"""Small diagnostic reader for EXPcalibur v4 replay files."""

from __future__ import annotations

import math
import struct
import sys
from dataclasses import dataclass


class Reader:
    def __init__(self, data: bytes, pos: int = 0):
        self.data = data
        self.pos = pos

    def take(self, n: int) -> bytes:
        out = self.data[self.pos : self.pos + n]
        if len(out) != n:
            raise ValueError("truncated replay")
        self.pos += n
        return out

    def unpack(self, fmt: str):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.take(size))[0]

    def u8(self): return self.unpack("<B")
    def i16(self): return self.unpack("<h")
    def u16(self): return self.unpack("<H")
    def u32(self): return self.unpack("<I")
    def u64(self): return self.unpack("<Q")

    def varint(self):
        value = 0
        shift = 0
        while True:
            b = self.u8()
            value |= (b & 0x7f) << shift
            if not b & 0x80:
                return value
            shift += 7
            if shift >= 70:
                raise ValueError("malformed varint")

    def zz(self):
        value = self.varint()
        return (value >> 1) ^ -(value & 1)


def signed(value: int, bits: int) -> int:
    mask = (1 << bits) - 1
    value &= mask
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def entity():
    return {
        "ty": 0, "x": 0, "y": 0, "vx": 0, "vy": 0,
        "hp_frac": 0, "hp": 0, "max_hp": 0, "value": 0,
        "pvx": 0, "pvy": 0, "tg_kind": 0,
    }


def extra(r: Reader, cls: int, item: dict):
    if cls == 0:
        item["hp_frac"] = r.u8()
    elif cls == 1:
        item["hp"] = signed(r.zz(), 32)
        item["max_hp"] = signed(r.zz(), 32)
        item["tg_kind"] = r.u8()
        if item["tg_kind"]:
            for name in ("tg_x", "tg_y", "tg_a", "tg_r", "tg_len", "tg_w", "tg_ha"):
                item[name] = r.zz()
            item["tg_t"] = r.varint()
            item["tg_dur"] = r.varint()
    elif cls == 2:
        item["value"] = r.varint() & 0xffffffff
    elif cls == 3:
        item["pvx"] = r.i16()
        item["pvy"] = r.i16()


def hero_full(r: Reader):
    return {
        "x": r.i16(), "y": r.i16(), "hp": signed(r.zz(), 32),
        "max_hp": signed(r.zz(), 32), "level": r.varint() & 0xffff,
        "xp_into": r.varint() & 0xffffffff, "xp_to_next": r.varint() & 0xffffffff,
        "total_exp": r.varint() & ((1 << 64) - 1),
        "kills": r.varint() & 0xffffffff, "aim_brad": r.u16(),
        "swing_cd": r.u8(), "swing_dmg": r.i16(),
    }


def hero_delta(r: Reader, old: dict):
    out = dict(old)
    out["x"] = signed(old["x"] + r.zz(), 16)
    out["y"] = signed(old["y"] + r.zz(), 16)
    flags = r.u8()
    fields = (
        (1, "hp", 32), (2, "max_hp", 32), (4, "level", 16),
        (8, "xp_into", 32), (16, "xp_to_next", 32),
        (32, "total_exp", 64), (64, "kills", 32),
    )
    for bit, name, bits in fields:
        if flags & bit:
            out[name] = signed(old[name] + r.zz(), bits) if name in ("hp", "max_hp") else (old[name] + r.zz()) & ((1 << bits) - 1)
    out["aim_brad"] = r.u16()
    out["swing_cd"] = r.u8()
    out["swing_dmg"] = r.i16()
    return out


def events(r: Reader):
    names = ("Kill", "LevelUp", "Pickup", "BossSpawn", "HeroDeath", "Debug", "Steal")
    out = []
    for _ in range(r.varint()):
        kind = r.u8()
        if kind == 0:
            out.append(("Kill", r.varint(), r.u8(), r.varint()))
        elif kind == 1:
            out.append(("LevelUp", r.u8(), r.u8()))
        elif kind == 2:
            out.append(("Pickup", r.varint(), r.u8(), r.varint()))
        elif kind == 3:
            out.append(("BossSpawn", r.varint(), r.u8()))
        elif kind == 4:
            out.append(("HeroDeath",))
        elif kind == 5:
            out.append(("Debug", r.take(r.varint())))
        elif kind == 6:
            out.append(("Steal", r.varint(), r.varint(), r.varint()))
        else:
            raise ValueError(f"bad event {kind}")
    return out


def classes_delta(r: Reader, cls: int, current: dict):
    additions = []
    for _ in range(r.varint()):
        slot = r.varint() & 0xffff
        item = entity()
        item.update(ty=r.u8(), x=r.i16(), y=r.i16())
        extra(r, cls, item)
        additions.append((slot, item))

    slot = 0
    for _ in range(r.varint()):
        slot = (slot + r.varint()) & 0xffff
        current.pop(slot, None)

    keys = sorted(current)
    mask = r.take((len(keys) + 7) >> 3)
    for idx, slot in enumerate(keys):
        item = current[slot]
        predicted_x = item["x"] + item["vx"]
        predicted_y = item["y"] + item["vy"]
        dx = dy = 0
        if mask[idx >> 3] & (1 << (idx & 7)):
            dx, dy = signed(r.zz(), 32), signed(r.zz(), 32)
        new_x, new_y = predicted_x + dx, predicted_y + dy
        item["vx"], item["vy"] = new_x - item["x"], new_y - item["y"]
        item["x"], item["y"] = signed(new_x, 16), signed(new_y, 16)

    if cls == 0:
        hp_mask = r.take((len(keys) + 7) >> 3)
        for idx, slot in enumerate(keys):
            if hp_mask[idx >> 3] & (1 << (idx & 7)):
                current[slot]["hp_frac"] = r.u8()
    elif cls == 1:
        slot = 0
        for _ in range(r.varint()):
            slot = (slot + r.varint()) & 0xffff
            extra(r, cls, current[slot])

    for slot, item in additions:
        current[slot] = item


@dataclass
class State:
    hero: dict
    classes: list[dict]


def parse(path: str):
    data = open(path, "rb").read()
    r = Reader(data)
    if r.take(4) != b"EXRP":
        raise ValueError("bad replay magic")
    version = r.u16()
    flags, tick_rate, qscale, tick_count = r.u16(), r.u16(), r.u16(), r.u32()
    seed, bot_hash = r.u64(), r.take(32)
    map_ref, map_w, map_h = r.u32(), r.u32(), r.u32()
    final_exp, final_level, final_kills, final_tick = r.u64(), r.u16(), r.u32(), r.u32()
    keyframe_ivl, index_off = r.u16(), r.u64()
    if version == 4:
        key_id, ruleset_id, engine_version = r.u32(), r.u32(), r.u32()
    index = Reader(data, index_off)
    blocks = [(index.u32(), index.u64(), index.u32()) for _ in range(index.u32())]
    header = locals()
    frames = []
    for start_tick, off, length in blocks:
        block = Reader(data[off : off + length])
        event_flag = block.u8()
        state = State(hero_full(block), [dict() for _ in range(4)])
        for cls in range(4):
            count = block.varint()
            slot = 0
            for _ in range(count):
                slot = (slot + block.varint()) & 0xffff
                item = entity()
                item.update(ty=block.u8(), x=block.i16(), y=block.i16())
                extra(block, cls, item)
                state.classes[cls][slot] = item
        ev = events(block) if event_flag & 2 else []
        frames.append((start_tick, dict(state.hero), state.classes, ev))
        tick = start_tick
        while block.pos < len(block.data):
            tick += 1
            event_flag = block.u8()
            state.hero = hero_delta(block, state.hero)
            for cls in range(4):
                classes_delta(block, cls, state.classes[cls])
            ev = events(block) if event_flag & 2 else []
            frames.append((tick, dict(state.hero), state.classes, ev))
    return header, frames


def nearest(hero, items):
    if not items:
        return -1
    return int(min(math.hypot(v["x"] - hero["x"], v["y"] - hero["y"]) for v in items.values()))


def main():
    header, frames = parse(sys.argv[1])
    print(f"version={header['version']} seed=0x{header['seed']:08x} ticks={header['tick_count']} "
          f"final_exp={header['final_exp']} level={header['final_level']} kills={header['final_kills']}")
    print("tick   pos        hp       lvl exp    kills enemies gems proj nearE nearG dmg")
    previous_hp = None
    damage_total = 0
    for tick, hero, classes, ev in frames:
        damage = 0 if previous_hp is None else max(0, previous_hp - hero["hp"])
        previous_hp = hero["hp"]
        damage_total += damage
        important = damage or ev or tick % 300 == 0 or tick == frames[-1][0]
        if important:
            labels = ",".join(e[0] for e in ev)
            print(f"{tick:5d} ({hero['x']:4d},{hero['y']:4d}) {hero['hp']:4d}/{hero['max_hp']:<4d} "
                  f"{hero['level']:3d} {hero['total_exp']:6d} {hero['kills']:5d} "
                  f"{len(classes[0]):7d} {len(classes[2]):4d} {len(classes[3]):4d} "
                  f"{nearest(hero, classes[0]):5d} {nearest(hero, classes[2]):5d} "
                  f"{damage:3d} {labels}")
    print(f"total_damage={damage_total}")


if __name__ == "__main__":
    main()
