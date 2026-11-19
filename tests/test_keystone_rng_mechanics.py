"""Keystone testbed: an isolated RandomStream for presentation-only variety.

`rng` was one of the Keystone modules the shooter never imported. The sim owns
two random.Random streams for combat and rewards; this stream is forked away
from them so a presentation draw can never move the deterministic sim hash.
"""

from keystone.rng import RandomStream
from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game(seed: int = 1) -> ShooterGame:
    g = ShooterGame()
    g.sim.seed = seed
    g.build_scene()
    return g


def test_presentation_draws_are_reproducible_and_seed_dependent():
    a = [_game()._presentation_gain(0.7) for _ in range(8)]
    b = [_game()._presentation_gain(0.7) for _ in range(8)]
    other = [_game(seed=7)._presentation_gain(0.7) for _ in range(8)]
    assert a == b
    assert a != other
    assert all(0.665 <= value <= 0.735 for value in a)


def test_presentation_draws_cannot_touch_the_sim_hash():
    g = _game()
    before = stable_hash(g.sim.snapshot())
    for _ in range(200):
        g._presentation_gain(0.7)
    assert stable_hash(g.sim.snapshot()) == before
    assert stable_hash(g.sim.snapshot()) == stable_hash(_game().sim.snapshot())


def test_the_json_state_restores_the_exact_next_draw():
    g = _game()
    state = g.presentation_rng_report()["stream"]
    drawn = [g._presentation_gain(0.7) for _ in range(8)]
    restored = RandomStream.from_snapshot(state)
    assert [0.7 * restored.uniform(0.95, 1.05) for _ in range(8)] == drawn


def test_a_rebuild_reseeds_the_stream():
    g = _game()
    for _ in range(5):
        g._presentation_gain(0.7)
    g.build_scene()
    assert g._presentation_gain(0.7) == _game()._presentation_gain(0.7)


def test_the_shoot_voice_actually_draws_from_the_stream():
    g = _game()
    seen: list[float] = []
    g.set_clip_hook(lambda clip, gain: seen.append(float(gain)))
    probe = RandomStream.from_snapshot(g.presentation_rng_report()["stream"])
    expected = 0.7 * probe.uniform(0.95, 1.05)
    g._play_event("shoot")
    assert seen == [expected], (seen, expected)
