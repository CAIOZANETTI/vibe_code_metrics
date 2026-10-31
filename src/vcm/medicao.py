"""Medições de processo portáveis (Linux, macOS e Windows)."""

from __future__ import annotations

import sys


def pico_ram_mb() -> float | None:
    """Pico de memória residente do processo atual, em MB (MiB).

    Linux: `ru_maxrss` em KiB; macOS: em bytes; Windows: `psutil` (pico do working set),
    se instalado. Devolve None quando não há como medir.
    """
    try:
        import resource
    except ImportError:  # Windows
        try:
            import psutil
        except ImportError:
            return None
        return psutil.Process().memory_info().peak_wset / 2**20
    pico = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return pico / 2**20 if sys.platform == "darwin" else pico / 1024
