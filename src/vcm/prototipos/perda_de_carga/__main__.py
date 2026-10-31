"""`python -m vcm.prototipos.perda_de_carga`: roda o benchmark e gera o relatório."""

from vcm.prototipos.perda_de_carga.relatorio import gerar_relatorio
from vcm.prototipos.perda_de_carga.rodar import rodar


def principal() -> None:
    rodar()
    print(gerar_relatorio())


if __name__ == "__main__":
    principal()
