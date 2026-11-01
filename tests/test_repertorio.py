"""Valida o formato do repertório: campos, papéis e referências cruzadas."""

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1] / "repertorio"
CAMPOS = {
    "id", "nome", "papel", "descricao", "quando_considerar", "quando_evitar", "cuidados",
    "coopera_com", "compete_com", "pacote_python", "documentacao", "evidencias", "status",
}  # fmt: skip
PAPEIS = {"calculo", "tabular", "armazenamento", "grafos", "intercambio", "apresentacao"}
STATUS = {"em_uso", "em_teste", "candidato", "rejeitado"}


def _entradas() -> dict[str, dict]:
    entradas = {}
    for arquivo in sorted(RAIZ.glob("*/*.yaml")):
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
