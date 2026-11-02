"""Valida o formato do repertório: campos, papéis e referências cruzadas."""

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1] / "repertorio"
CAMPOS = {
    "id", "nome", "papel", "descricao", "quando_considerar", "quando_evitar", "cuidados",
    "coopera_com", "compete_com", "pacote_python", "documentacao", "evidencias", "status",
    "repositorio", "licenca", "ultima_versao", "verificado_em",
}  # fmt: skip
PAPEIS = {
    "calculo", "tabular", "armazenamento", "validacao", "geoespacial", "cad_3d", "grafos",
    "intercambio", "documentos", "apresentacao", "qualidade",
}  # fmt: skip
STATUS = {"em_uso", "em_teste", "candidato", "rejeitado"}


def _entradas() -> dict[str, dict]:
    entradas = {}
    for arquivo in sorted(RAIZ.glob("*/*.yaml")):
        if arquivo.parent.name == "skills":
            continue
        dado = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        assert dado["id"] not in entradas, f"id repetido: {dado['id']}"
        assert arquivo.parent.name == dado["papel"], f"{arquivo} fora da pasta do papel"
        entradas[dado["id"]] = dado
    return entradas


def test_campos_papel_e_status():
    for id_, e in _entradas().items():
        assert set(e) == CAMPOS, f"{id_}: campos {set(e) ^ CAMPOS}"
        assert e["papel"] in PAPEIS and e["status"] in STATUS, id_


def test_so_compete_dentro_do_mesmo_papel_e_referencias_existem():
    entradas = _entradas()
    for id_, e in entradas.items():
        for outro in e["compete_com"]:
            assert entradas[outro]["papel"] == e["papel"], f"{id_} × {outro}"
        for outro in e["coopera_com"]:
            assert outro in entradas, f"{id_}: coopera com {outro} inexistente"


def test_catalogo_de_modelos_sem_preco_inventado():
    modelos = yaml.safe_load((RAIZ / "modelos.yaml").read_text(encoding="utf-8"))["modelos"]
    for m in modelos:
        if any(v is not None for v in m["preco_usd_por_mtok"].values()):
            assert m["verificado_em"] and m["fonte"], f"{m['id']}: preço sem data/fonte"


def test_precos_empacotados_iguais_ao_catalogo():
    """O vcm instalado em outro projeto usa a cópia empacotada; ela não pode divergir."""
    empacotado = Path(__file__).resolve().parents[1] / "src" / "vcm" / "modelos_precos.yaml"
    assert empacotado.read_bytes() == (RAIZ / "modelos.yaml").read_bytes(), (
        "copie repertorio/modelos.yaml para src/vcm/modelos_precos.yaml"
    )


def test_papeis_do_teste_iguais_aos_da_pagina():
    from vcm.repertorio import PAPEIS as PAPEIS_DA_PAGINA

    assert set(PAPEIS_DA_PAGINA) == PAPEIS


def test_licenca_e_versao_tem_data_de_verificacao():
    for id_, e in _entradas().items():
        if e["licenca"] or e["ultima_versao"]:
            assert e["verificado_em"], f"{id_}: licença/versão sem data de verificação"


CAMPOS_SKILL = [
    "id", "nome", "origem", "onde", "para_que", "quando_usar", "quando_evitar", "cuidados",
    "agente_sugerido", "ferramentas_relacionadas", "licenca", "verificado_em", "status",
]  # fmt: skip


def test_esquema_das_skills_e_ligacao_com_ferramentas():
    from vcm.repertorio import AGENTES, ORIGENS

    ferramentas = set(_entradas())
    vistos = set()
    for arquivo in sorted((RAIZ / "skills").glob("*.yaml")):
        s = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        assert list(s) == CAMPOS_SKILL, f"{arquivo.name}: campos {list(s)}"
        assert arquivo.stem == s["id"] and s["id"] not in vistos
        vistos.add(s["id"])
        assert s["origem"] in ORIGENS and s["status"] in STATUS
        assert s["agente_sugerido"] in (None, *AGENTES)
        if s["origem"] == "externa":
            assert s["id"].startswith("ext-") and s["onde"].startswith("https://")
        for f in s["ferramentas_relacionadas"]:
            assert f in ferramentas, f"{s['id']}: ferramenta {f} fora do repertório"
