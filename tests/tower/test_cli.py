import signal

import tower.cli


def test_main_restores_default_sigint_and_calls_native(monkeypatch):
    captured = {}

    def fake_signal(sig, handler):
        captured["sig"] = sig
        captured["handler"] = handler

    def fake_run_cli(argv):
        captured["argv"] = argv

    monkeypatch.setattr(tower.cli.signal, "signal", fake_signal)
    monkeypatch.setattr(tower.cli, "_run_cli", fake_run_cli)

    tower.cli.main()

    assert captured["sig"] == signal.SIGINT
    assert captured["handler"] == signal.SIG_DFL
    assert isinstance(captured["argv"], list)
    assert len(captured["argv"]) > 0
