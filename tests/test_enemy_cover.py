"""Enemy/cover proofs: melee enemies cannot walk through arena cover.

The baseline sim moved every enemy straight at the player; the player and
hitscan rays collided with covers, but mites/brutes/wisps passed through
them. This pins the slide-around behaviour and the spawn guard.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _inside_any_cover(sim: Sim, x: float, z: float, radius: float) -> bool:
    for c in sim.levels["arena"]["covers"]:
        if (abs(x - float(c["x"])) < float(c["w"]) / 2.0 + radius
                and abs(z - float(c["z"])) < float(c["d"]) / 2.0 + radius):
            return True
    return False


def _crossing_sim() -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    # player at spawn (0, 8); mite starts behind the centre cover at (0, 0)
    s.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, -2.0), hp=30, max_hp=30)]
    return s


def test_enemy_never_enters_cover():
    s = _crossing_sim()
    radius = float(s.enemy_defs["mite"]["radius"])
    entered = False
    for _ in range(120):
        s.step(1.0 / 60.0, ActionState())
        e = s.enemies[0]
        if _inside_any_cover(s, e.pos.x, e.pos.z, radius - 1e-6):
            entered = True
            break
    assert entered is False, (s.enemies[0].pos.x, s.enemies[0].pos.z)


def test_enemy_gets_around_cover_toward_player():
    s = _crossing_sim()
    for _ in range(240):
        s.step(1.0 / 60.0, ActionState())
    e = s.enemies[0]
    # it must not remain parked on the far side forever
    assert e.pos.z > 1.4 or abs(e.pos.x) > 1.4, (e.pos.x, e.pos.z)


def test_spawn_guard_keeps_enemies_out_of_covers():
    s = Sim(seed=7)
    s.spawn_queue = ["mite"] * 30
    s.spawn_t = 0.0
    for _ in range(30):
        s._spawn_enemy("mite")
    for e in s.enemies:
        assert not _inside_any_cover(s, e.pos.x, e.pos.z, float(s.enemy_defs[e.etype]["radius"])), e.pos
