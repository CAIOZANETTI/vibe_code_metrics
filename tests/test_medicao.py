"""Medição de memória portável: Linux, macOS e Windows (simulados)."""

import sys

import pytest

from vcm import medicao


def test_linux_kib_para_mib():
    valor = medicao.pico_ram_mb()
    assert valor is not None and 1.0 < valor < 100_000.0


def test_macos_bytes_para_mib(monkeypatch):
    import resource

    class Uso:
        ru_maxrss = 50 * 2**20  # 50 MiB em bytes, como no macOS

    monkeypatch.setattr(resource, "getrusage", lambda _: Uso())
    monkeypatch.setattr(sys, "platform", "darwin")
    assert medicao.pico_ram_mb() == pytest.approx(50.0)


def test_windows_sem_resource_usa_psutil(monkeypatch):
    import types

    class Memoria:
        peak_wset = 80 * 2**20  # atributo que só existe no Windows (bytes)

    psutil_falso = types.SimpleNamespace(
        Process=lambda: types.SimpleNamespace(memory_info=lambda: Memoria())
    )
    monkeypatch.setitem(sys.modules, "resource", None)  # import resource -> ImportError
    monkeypatch.setitem(sys.modules, "psutil", psutil_falso)
    assert medicao.pico_ram_mb() == pytest.approx(80.0)


def test_windows_sem_resource_nem_psutil_devolve_none(monkeypatch):
    monkeypatch.setitem(sys.modules, "resource", None)
    monkeypatch.setitem(sys.modules, "psutil", None)
    assert medicao.pico_ram_mb() is None
