"""Combat-feel proofs: non-lethal hits visibly flinch the enemy.

The sim only stores a short `hit_t`; the game applies a squash + push away
from the player in `_sync_scene`. Damage, hitboxes, movement and the snapshot
are untouched.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy


def _hit_sim(hp: int = 30) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=hp, max_hp=30)]
    s.yaw = 0.0
    s.pitch = 0.0
    s._fire(s.weapons["pulse"], [])
    return s


def test_nonlethal_hit_sets_flinch_timer():
    s = _hit_sim(30)
    enemy = s.enemies[0]
    assert enemy.hp == 18
    assert enemy.hit_t > 0.0
    assert "hit_t" not in s.snapshot()


def test_flinch_expires_without_changing_damage():
    s = _hit_sim(30)
    hp = s.enemies[0].hp
    for _ in range(60):
        s.step(1.0 / 60.0, ActionState())
    assert s.enemies[0].hit_t == 0.0
    assert s.enemies[0].hp == hp


def test_sync_scene_squashes_and_pushes_flinching_enemy():
    g = ShooterGame()
    g.build_scene()
    g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=18, max_hp=30,
                            hit_t=0.25)]
    g._sync_scene()
    node = g._enemy_nodes[0]
    assert node.visible is True
    assert node.transform.scale.x > node.transform.scale.y
    assert node.transform.position.z < 2.0
    assert node.material is g.assets.require("material.enemy_hit").payload
    g.sim.enemies[0].hit_t = 0.0
    g._sync_scene()
    assert node.transform.scale.x == node.transform.scale.y
    assert node.transform.position.z == 2.0
    assert node.material is g.assets.require("material.mite").payload
