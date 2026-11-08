"""Keystone mechanics testbed: replay, triggers, particles, batching, grid.

These tests drive the same engine systems the shooter uses in play, so a
keystone regression in a mechanic fails the project suite directly.
"""

from pathlib import Path

from keystone.batch import plan_batches
from keystone.input import ActionState
from keystone.math3d import Vec3
from keystone.physics import AABB
from keystone.replay import CommandLog, run_log, verify_log
from keystone.triggers import TriggerTracker, TriggerVolume

from shooter.game import ShooterGame
from shooter.sim import Sim

ROOT = Path(__file__).parent.parent


def test_replay_runner_verifies_the_campaign_win():
    log = CommandLog.load(ROOT / "bot_campaign.json")
    single = run_log(ShooterGame, log)
    assert single["ok"] is True, single
    assert single["hash"] == "bb425a57b9839e001906cff227fb618f", single["hash"]
    assert single["frames"] == 3000, single["frames"]
    final = single["final"]
    assert final["outcome"] == "win", final["outcome"]
    assert final["wave"] == 4, final["wave"]
    assert final["kills"] == 30, final["kills"]
    assert final["score"] == 11560, final["score"]
    assert final["player"]["hp"] == 38, final["player"]["hp"]

    prefix = CommandLog(
        seed=log.seed, step=log.step, frames=list(log.frames[:300])
    )
    verified = verify_log(ShooterGame, prefix)
    assert verified["ok"] is True, verified
    assert verified["first"]["tick"] == 300, verified["first"]["tick"]


def test_trigger_tracker_enters_once_and_exits():
    tracker = TriggerTracker()
    volume = TriggerVolume("surge", AABB(Vec3(0.0, 0.5, -6.0), Vec3(1.0, 0.5, 1.0)))
    inside = AABB(Vec3(0.0, 0.9, -6.0), Vec3(0.35, 0.9, 0.35))
    outside = AABB(Vec3(5.0, 0.9, 5.0), Vec3(0.35, 0.9, 0.35))

    first = tracker.update(inside, [volume])
    assert first.entered == ("surge",), first
    assert "surge" in first.active
    held = tracker.update(inside, [volume])
    assert held.entered == (), held
    assert "surge" in held.active
    left = tracker.update(outside, [volume])
    assert left.exited == ("surge",), left
    assert not left.active


def test_pickup_trigger_fires_once():
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = []
    s.pickup_active = True
    s.pickup_taken = False
    rest_y = float(s.player_pos.y)
    s.player_pos = Vec3(0.0, rest_y, -6.0)
    s.body = s.body.__class__(
        position=Vec3(0.0, rest_y, -6.0), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.hvel = Vec3()

    events = s.step(1.0 / 60.0, ActionState())
    assert "pickup" in events, events
    assert s.weapon == "surge"
    assert s.pickup_taken is True
    assert s.pickup_active is False
    ammo = int(s.ammo["surge"])

    again = s.step(1.0 / 60.0, ActionState())
    assert "pickup" not in again, again
    assert int(s.ammo["surge"]) == ammo


def test_particle_burst_is_deterministic():
    def burst():
        s = Sim(seed=1)
        added = s.particles.burst("impact", 12, Vec3(0.0, 1.0, 0.0))
        alive = s.particles.step(1.0 / 60.0)
        trail = [
            (
                round(p.position.x, 6), round(p.position.y, 6), round(p.position.z, 6),
                round(p.velocity.x, 6), round(p.velocity.y, 6), round(p.velocity.z, 6),
                round(p.age, 6), p.emitter,
            )
            for p in s.particles.particles
        ]
        return added, alive, trail

    first = burst()
    second = burst()
    assert first[0] == 12 and first[1] == 12, first[:2]
    assert first == second


def test_scene_batches_plan_shared_static_groups():
    g = ShooterGame()
    g.build_scene()
    plan = plan_batches(g.scene)
    assert plan["groups"] == 8, plan["groups"]
    assert plan["draw_calls"] == 35, plan["draw_calls"]
    assert plan["batched_calls"] == 8, plan["batched_calls"]
    assert plan["saved_calls"] == 27, plan["saved_calls"]
    assert plan["triangles"] == 494, plan["triangles"]
    assert any("platform-pad" in batch["nodes"] for batch in plan["batches"])


def test_spatial_grid_broadphase_matches_colliders():
    s = Sim(seed=1)
    assert len(s.grid) == len(s.colliders)
    cover_hit = s.grid.query(
        AABB(Vec3(-6.0, 0.75, -4.0), Vec3(0.1, 0.1, 0.1))
    )
    assert cover_hit, cover_hit
    assert all(str(key).startswith("wall:") for key in cover_hit)
    far_above = AABB(Vec3(18.0, 5.0, 18.0), Vec3(0.1, 0.1, 0.1))
    assert s.grid.query(far_above) == []
