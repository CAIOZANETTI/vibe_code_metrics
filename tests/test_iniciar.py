"""Testes do comando `vcm iniciar`."""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from vcm import iniciar as modulo_iniciar
from vcm.cli import main

RAIZ = Path(__file__).resolve().parents[1]


def _status(itens):
    return {caminho.name: status for caminho, status in itens}


def test_cria_tudo(tmp_path):
    destino = tmp_path / "meu-projeto"
    itens = modulo_iniciar.iniciar(destino, "calculo")
    assert all(status == "criado" for _, status in itens)
    for relativo in [
        "vcm.yaml",
        "CLAUDE.md",
        "docs/estilo.md",
        ".claude/agents/executor-sonnet.md",
        ".claude/agents/executor-haiku.md",
        "src/calculo/__init__.py",
        "src/calculo/referencia.py",
        "tests/test_referencia.py",
        ".github/workflows/vcm.yml",
        ".gitignore",
    ]:
        assert (destino / relativo).is_file(), relativo
    assert "model: sonnet" in (destino / ".claude/agents/executor-sonnet.md").read_text()
    assert "model: haiku" in (destino / ".claude/agents/executor-haiku.md").read_text()
    fluxo = (destino / ".github/workflows/vcm.yml").read_text()
    assert "${{ github.event.pull_request.base.sha }}" in fluxo
    assert "--falhar-se-reverter" in fluxo


def test_segunda_execucao_nao_sobrescreve_e_forcar_sobrescreve(tmp_path):
    modulo_iniciar.iniciar(tmp_path, "calculo")
    (tmp_path / "CLAUDE.md").write_text("meu texto", encoding="utf-8")
    itens = modulo_iniciar.iniciar(tmp_path, "calculo")
    assert (tmp_path / "CLAUDE.md").read_text() == "meu texto"
    assert _status(itens)["CLAUDE.md"] == "mantido (já existia)"
    itens = modulo_iniciar.iniciar(tmp_path, "calculo", forcar=True)
    assert _status(itens)["CLAUDE.md"] == "sobrescrito"
    assert (tmp_path / "CLAUDE.md").read_text() != "meu texto"


def test_gitignore_sem_duplicar(tmp_path):
    (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    modulo_iniciar.iniciar(tmp_path, "calculo")
    modulo_iniciar.iniciar(tmp_path, "calculo")
    linhas = (tmp_path / ".gitignore").read_text().splitlines()
    assert sorted(linhas) == sorted([".venv/", "__pycache__/", ".claude/worktrees/"])


def test_vcm_yaml_segue_o_esquema(tmp_path):
    destino = tmp_path / "prototipo"
    modulo_iniciar.iniciar(destino, "calculo")
    config = yaml.safe_load((destino / "vcm.yaml").read_text(encoding="utf-8"))
    assert config == {
        "projeto": "prototipo",
        "pastas_fonte": ["src"],
        "pasta_testes": "tests",
        "referencia": {"comando": ["python", "-m", "calculo.referencia"], "repeticoes": 5},
        "limites": {},
    }


def test_referencia_gerada_executa(tmp_path):
    modulo_iniciar.iniciar(tmp_path, "calculo")
    ambiente = {**os.environ, "PYTHONPATH": str(tmp_path / "src")}
    saida = subprocess.run(
        [sys.executable, "-m", "calculo.referencia"],
        cwd=tmp_path,
        env=ambiente,
        capture_output=True,
        text=True,
        check=True,
    )
    dados = json.loads(saida.stdout.strip().splitlines()[-1])
    assert set(dados) == {"hash", "tempo_ms", "pico_ram_mb"}
    assert len(dados["hash"]) == 64


def test_estilo_do_repositorio_igual_ao_modelo_empacotado():
    canonico = modulo_iniciar.PASTA_MODELOS / "estilo.md"
    assert (RAIZ / "docs" / "estilo.md").read_bytes() == canonico.read_bytes(), (
        "docs/estilo.md divergiu de src/vcm/modelos_projeto/estilo.md; mantenha as duas iguais"
    )


def test_cli_iniciar_imprime_lista_e_proximos_passos(tmp_path, capsys):
    codigo = main(["iniciar", str(tmp_path / "p"), "--pacote", "calculo"])
    saida = capsys.readouterr().out
    assert codigo == 0
    assert "vcm.yaml -> criado" in saida
    assert "Próximos passos" in saida
    assert "git init" in saida and "uv add numpy pandas" in saida
    assert "vcm balanco HEAD~1 HEAD" in saida


def test_referencia_gerada_funciona_sem_resource(tmp_path):
    """Simula Windows sem psutil: o JSON sai com pico_ram_mb = null, sem quebrar."""
    import json
    import subprocess
    import sys

    from vcm.iniciar import iniciar

    iniciar(tmp_path, "calculo")
    codigo = (
        "import sys; sys.modules['resource'] = None; sys.modules['psutil'] = None; "
        "import runpy; runpy.run_module('calculo.referencia', run_name='__main__')"
    )
    saida = (
        subprocess.run(
            [sys.executable, "-c", codigo],
            check=True,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(tmp_path / "src")},
        )
        .stdout.strip()
        .splitlines()[-1]
    )
    dado = json.loads(saida)
    assert dado["pico_ram_mb"] is None and len(dado["hash"]) == 64
