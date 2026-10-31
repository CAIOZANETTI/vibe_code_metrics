import pandas as pd
import pytest

from vcm import ruido
from vcm.balanco import balanco


def test_estimar_ruido_por_repeticao(tmp_path):
    medicoes = pd.DataFrame(
        {"tempo_referencia_ms": [100.0, 110.0, 90.0], "sloc_por_funcao": [10.0, 10.0, 10.0]}
    )
    r = ruido.estimar(medicoes)
    assert r.loc["sloc_por_funcao", "ruido_relativo"] == 0.0
    assert r.loc["tempo_referencia_ms", "coef_variacao"] == pytest.approx(0.1)
    assert r.loc["tempo_referencia_ms", "ruido_relativo"] == pytest.approx(0.2)
    arq = ruido.gravar(r, tmp_path / "ruido.parquet")
    assert ruido.carregar(arq)["tempo_referencia_ms"] == pytest.approx(0.2)
    assert ruido.carregar(tmp_path / "nao_existe.parquet") is None


def test_ruido_medido_alarga_a_faixa_de_igual():
    antes = pd.Series({"tempo_referencia_ms": 100.0})
    depois = pd.Series({"tempo_referencia_ms": 82.0})  # 18% mais rápido
    assert balanco(antes, depois).loc["tempo_referencia_ms", "veredito"] == "melhorou"
    medido = pd.Series({"tempo_referencia_ms": 0.25})  # ruído medido de 25%
    t = balanco(antes, depois, ruido_medido=medido)
    assert t.loc["tempo_referencia_ms", "veredito"] == "igual"
    assert t.loc["tempo_referencia_ms", "ruido_pct"] == pytest.approx(25.0)
