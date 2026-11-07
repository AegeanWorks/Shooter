"""Combat-feedback proofs: damage source tracking and HUD direction cue.

The baseline hid the attacker's direction entirely: HP dropped and the
snapshot carried no source, so a hurt from the left, right and behind was
indistinguishable. These tests pin the source/time telemetry and the
presentation-only edge cue (no sim change).
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy
from shooter.ui import draw_shooter


class _Canvas:
    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


class _Hud:
    width = 960
    height = 540


def _parked_with_mite(x: float, z: float) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]  # non-empty queue blocks the wave-clear bonus
    s.spawn_t = 999.0
    s.enemies = [_Enemy(etype="mite", pos=Vec3(x, 0.5, z), hp=30, max_hp=30)]
    return s


def test_hurt_records_source_and_timer():
    s = _parked_with_mite(0.8, 8.0)
    hp0 = int(s.hp)
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) < hp0 and "hurt" in events, events
    assert float(s.hurt_t) > 0.0
    # source is the attacker position at hit time, not the player position
    assert abs(s.hurt_from.x - s.enemies[0].pos.x) < 1e-6
    assert abs(s.hurt_from.z - s.enemies[0].pos.z) < 1e-6
    snap = s.snapshot()
    assert snap["hurt"]["t"] > 0.0
    assert snap["hurt"]["x"] == round(float(s.hurt_from.x), 4)


def test_hurt_cue_expires():
    s = _parked_with_mite(0.8, 8.0)
    s.step(1.0 / 60.0, ActionState())
    assert float(s.hurt_t) > 0.0
    s.enemies = []
    for _ in range(60):
        s.step(1.0 / 60.0, ActionState())
    assert float(s.hurt_t) == 0.0
    assert s.snapshot()["hurt"]["t"] == 0.0


def _red_rects(canvas: _Canvas) -> list[tuple]:
    return [r for r in canvas.rects if r[4][0] >= 0.9 and r[4][1] <= 0.45 and r[4][2] <= 0.45]


def _draw_with_source(side: str) -> _Canvas:
    s = Sim(seed=1)
    s.hp = 100
    s.hurt_t = 0.5
    x, z = s.player_pos.x, s.player_pos.z
    if side == "left":
        x -= 5.0
    elif side == "right":
        x += 5.0
    else:
        z += 5.0
    s.hurt_from = Vec3(x, 0.5, z)
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    return canvas


def test_hud_draws_directional_damage_cue():
    cx, cy = _Hud.width / 2, _Hud.height / 2
    right = _red_rects(_draw_with_source("right"))
    assert right, "right-side hit drew no red cue"
    assert any(r[0] > cx + 60 for r in right), right
    left = _red_rects(_draw_with_source("left"))
    assert left, "left-side hit drew no red cue"
    assert any(r[0] < cx - 60 for r in left), left
    behind = _red_rects(_draw_with_source("behind"))
    assert behind, "behind hit drew no red cue"
    assert any(r[1] > cy + 60 for r in behind), behind


def test_hud_hides_damage_cue_when_quiet():
    s = Sim(seed=1)
    s.hp = 100
    s.hurt_t = 0.0
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    assert _red_rects(canvas) == []


def test_hurt_cue_does_not_change_sim_hash_path():
    # Two runs that take the same damage must stay deterministic even with
    # the new transient cue fields in the snapshot.
    from keystone.replay import stable_hash

    def run() -> str:
        g = ShooterGame()
        g.build_scene()
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.8, 0.5, 8.0), hp=30, max_hp=30)]
        for _ in range(90):
            g.update(1.0 / 60.0, ActionState())
        return stable_hash(g.snapshot())

    assert run() == run()
