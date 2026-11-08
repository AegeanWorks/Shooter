"""Level proof: a cleared campaign does not start wave 4 combat.

The banner appears when wave 3's warden dies, but the sim had already built
wave 4 and kept spawning it during the victory beat. The run is recorded as
a win while fresh enemies can attack the player; clearing the campaign must
seal the wave queue.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _win_game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.spawn_t = 999.0
    g.sim.pickup_taken = True
    g.sim.wave = 3
    g.sim.score = 5000
    g.sim.kills = 20
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=12,
               max_hp=600, summon_cd=999.0)
    ]
    for _ in range(60):
        g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
        if g.sim.wave >= 4:
            break
    assert g.sim.wave >= 4, g.sim.wave
    return g


def test_campaign_clear_seals_future_waves():
    g = _win_game()
    assert g.campaign_cleared is True
    assert g.sim.victory is True
    assert g.sim.spawn_queue == []
    wave = int(g.sim.wave)
    for _ in range(200):
        g.update(1.0 / 60.0, ActionState())
    assert int(g.sim.wave) == wave
    assert not any(e.alive for e in g.sim.enemies)
    assert g.sim.alive is True and g.sim.hp == 100
