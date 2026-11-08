"""UI proof: critical kills stay marked in the persistent kill feed.

The transient CRITICAL caption fades, and the kill feed kept only a generic
`MITE +220`; the reward record was indistinguishable from a normal kill.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


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


def _kill_game(critical: bool) -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.engagement["reward"] = {
        "standard_p": 0.0 if critical else 1.0,
        "critical_p": 1.0 if critical else 0.0,
        "critical_mult": 2.0,
        "cache_p": 0.0,
        "cache_reserve": 12,
        "cache_expire_s": 8.0,
    }
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=1, max_hp=30)
    ]
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    return g


def test_critical_kill_is_tagged_and_accented_in_the_feed():
    g = _kill_game(True)
    entry = g.kill_feed[0]
    assert entry["text"].startswith("CRIT MITE +"), entry
    assert entry.get("critical") is True, entry
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    feed = [t for t in canvas.texts if "CRIT MITE +" in str(t[2])]
    assert feed, canvas.texts
    assert feed[0][3][:3] == (1.0, 0.62, 0.20), feed[0][3]


def test_normal_kill_keeps_the_plain_feed_entry():
    g = _kill_game(False)
    entry = g.kill_feed[0]
    assert entry["text"].startswith("MITE +"), entry
    assert not entry.get("critical"), entry
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    feed = [t for t in canvas.texts if "MITE +" in str(t[2])]
    assert feed, canvas.texts
    assert feed[0][3][:3] != (1.0, 0.62, 0.20), feed[0][3]
