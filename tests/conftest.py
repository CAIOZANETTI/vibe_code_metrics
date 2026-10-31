"""Configuração comum dos testes."""


def pytest_configure(config):
    config.addinivalue_line("markers", "lento: teste lento (sobe subprocessos com uv)")
