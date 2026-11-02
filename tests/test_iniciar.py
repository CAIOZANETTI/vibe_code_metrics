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
        "dependencias_extras": [],
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


def _projeto_raiz(tmp_path):
    (tmp_path / "camadas").mkdir()
    (tmp_path / "camadas" / "__init__.py").write_text("# meu código\n", encoding="utf-8")
    return tmp_path


def test_layout_raiz_coloca_referencia_no_pacote(tmp_path):
    destino = _projeto_raiz(tmp_path)
    modulo_iniciar.iniciar(destino, "camadas")
    assert modulo_iniciar.detectar_layout(destino, "camadas") == "raiz"
    assert (destino / "camadas" / "referencia.py").is_file()
    assert (destino / "camadas" / "__init__.py").read_text() == "# meu código\n"
    assert not (destino / "src").exists()
    config = yaml.safe_load((destino / "vcm.yaml").read_text(encoding="utf-8"))
    assert config["pastas_fonte"] == ["camadas"]
    assert config["dependencias_extras"] == []
    assert "camadas" in (destino / "CLAUDE.md").read_text()
    assert not (destino / "pyproject.toml").exists()


def test_layout_src_quando_pacote_novo_ou_em_src(tmp_path):
    assert modulo_iniciar.detectar_layout(tmp_path, "calculo") == "src"
    (tmp_path / "src" / "calculo").mkdir(parents=True)
    (tmp_path / "calculo").mkdir()
    (tmp_path / "calculo" / "__init__.py").write_text("")
    assert modulo_iniciar.detectar_layout(tmp_path, "calculo") == "src"


def test_tem_pdca_liga_a_secao(tmp_path):
    modulo_iniciar.iniciar(tmp_path / "a", "calculo")
    assert "Integração com o PDCA" not in (tmp_path / "a" / "CLAUDE.md").read_text()
    (tmp_path / "b" / "pdca").mkdir(parents=True)
    modulo_iniciar.iniciar(tmp_path / "b", "calculo")
    texto = (tmp_path / "b" / "CLAUDE.md").read_text()
    assert "Integração com o PDCA" in texto and "reprodutibilidade" in texto


def test_gitignore_existente_recebe_so_o_que_falta(tmp_path):
    (tmp_path / ".gitignore").write_text("dados/\n__pycache__/\n", encoding="utf-8")
    modulo_iniciar.iniciar(tmp_path, "calculo")
    linhas = (tmp_path / ".gitignore").read_text().splitlines()
    assert linhas == ["dados/", "__pycache__/", ".venv/", ".claude/worktrees/"]


def test_claude_md_existente_nao_e_tocado_no_layout_raiz(tmp_path):
    destino = _projeto_raiz(tmp_path)
    (destino / "CLAUDE.md").write_text("convenções do projeto", encoding="utf-8")
    itens = modulo_iniciar.iniciar(destino, "camadas")
    assert (destino / "CLAUDE.md").read_text() == "convenções do projeto"
    assert _status(itens)["CLAUDE.md"] == "mantido (já existia)"


def test_cli_layout_raiz_nao_sugere_uv_init(tmp_path, capsys):
    destino = _projeto_raiz(tmp_path)
    assert main(["iniciar", str(destino), "--pacote", "camadas"]) == 0
    saida = capsys.readouterr().out
    assert "uv init" not in saida
    assert "camadas/referencia.py" in saida and "vcm balanco HEAD~1 HEAD" in saida


def test_iniciar_instala_a_skill_vcm_rumo_e_ela_nao_diverge(tmp_path):
    from pathlib import Path

    from vcm.iniciar import iniciar

    iniciar(tmp_path, "calculo")
    instalada = tmp_path / ".claude" / "skills" / "vcm-rumo" / "SKILL.md"
    assert instalada.exists() and "name: vcm-rumo" in instalada.read_text(encoding="utf-8")
    raiz = Path(__file__).resolve().parents[1]
    empacotada = raiz / "src" / "vcm" / "modelos_projeto" / "skills" / "vcm-rumo" / "SKILL.md"
    deste_repo = raiz / ".claude" / "skills" / "vcm-rumo" / "SKILL.md"
    assert empacotada.read_bytes() == deste_repo.read_bytes()


def test_iniciar_instala_a_skill_vcm_formulario_e_ela_nao_diverge(tmp_path):
    from pathlib import Path

    from vcm.iniciar import iniciar

    iniciar(tmp_path, "calculo")
    instalada = tmp_path / ".claude" / "skills" / "vcm-formulario" / "SKILL.md"
    assert "name: vcm-formulario" in instalada.read_text(encoding="utf-8")
    assert "vcm-formulario" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    raiz = Path(__file__).resolve().parents[1]
    empacotada = raiz / "src" / "vcm" / "modelos_projeto" / "skills" / "vcm-formulario" / "SKILL.md"
    deste_repo = raiz / ".claude" / "skills" / "vcm-formulario" / "SKILL.md"
    assert empacotada.read_bytes() == deste_repo.read_bytes()


COMANDO_GANCHO = "vcm formulario --verificar"


def _comandos_stop(caminho):
    configuracao = json.loads(caminho.read_text(encoding="utf-8"))
    return [g["command"] for grupo in configuracao["hooks"]["Stop"] for g in grupo["hooks"]]


def test_iniciar_cria_settings_com_gancho(tmp_path):
    itens = modulo_iniciar.iniciar(tmp_path, "calculo")
    assert _status(itens)["settings.json"] == "criado"
    assert _comandos_stop(tmp_path / ".claude/settings.json") == [COMANDO_GANCHO]


def test_iniciar_faz_merge_preservando_outras_chaves(tmp_path):
    caminho = tmp_path / ".claude" / "settings.json"
    caminho.parent.mkdir(parents=True)
    existente = {"permissions": {"allow": ["Bash(ls)"]}, "hooks": {"PreToolUse": [{"x": 1}]}}
    caminho.write_text(json.dumps(existente), encoding="utf-8")
    itens = modulo_iniciar.iniciar(tmp_path, "calculo", forcar=True)
    assert _status(itens)["settings.json"] == "atualizado"
    final = json.loads(caminho.read_text(encoding="utf-8"))
    assert final["permissions"] == existente["permissions"]
    assert final["hooks"]["PreToolUse"] == [{"x": 1}]
    assert _comandos_stop(caminho) == [COMANDO_GANCHO]


def test_iniciar_nao_duplica_gancho(tmp_path):
    modulo_iniciar.iniciar(tmp_path, "calculo")
    itens = modulo_iniciar.iniciar(tmp_path, "calculo", forcar=True)
    assert _status(itens)["settings.json"] == "mantido (já existia)"
    assert len(_comandos_stop(tmp_path / ".claude/settings.json")) == 1


def test_iniciar_reconhece_gancho_com_uv_run(tmp_path):
    caminho = tmp_path / ".claude" / "settings.json"
    caminho.parent.mkdir(parents=True)
    gancho = {"type": "command", "command": f"uv run --quiet {COMANDO_GANCHO}"}
    caminho.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [gancho]}]}}), encoding="utf-8")
    itens = modulo_iniciar.iniciar(tmp_path, "calculo")
    assert _status(itens)["settings.json"] == "mantido (já existia)"


def test_iniciar_nao_toca_em_json_invalido(tmp_path):
    caminho = tmp_path / ".claude" / "settings.json"
    caminho.parent.mkdir(parents=True)
    caminho.write_text("{quebrado", encoding="utf-8")
    itens = modulo_iniciar.iniciar(tmp_path, "calculo", forcar=True)
    assert _status(itens)["settings.json"].startswith("não alterado")
    assert caminho.read_text(encoding="utf-8") == "{quebrado"
