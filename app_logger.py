"""
App_Logger.py

Este módulo centraliza toda a lógica de logging da aplicação.
Configura o logger para escrever em 'logs/app.log' e
fornece funções para ler e limpar o arquivo de log.
"""

import logging
import os
import pathlib
from typing import Optional

# Define o diretório e o arquivo de log
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def _setup_logger() -> logging.Logger:
    """Configura e retorna o logger principal da aplicação."""

    # Garante que o diretório 'logs' exista
    pathlib.Path(LOG_DIR).mkdir(exist_ok=True)

    # Configura o logger
    logger = logging.getLogger('AppLogger')

    # Previne handlers duplicados se este módulo for importado várias vezes
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Cria o handler do arquivo
    # 'a' (append) - 'utf-8' (para caracteres especiais)
    handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')

    # Define o formato da mensagem: (Timestamp) - (Mensagem)
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Adiciona o handler ao logger
    logger.addHandler(handler)

    return logger


# Inicializa o logger para ser usado por outras funções
_logger = _setup_logger()


# --- Funções Públicas ---

def log_action(message: str):
    """
    Registra uma ação no arquivo de log.

    :param message: A mensagem a ser registrada.
    """
    try:
        _logger.info(message)
    except Exception as e:
        print(f"ERRO [app_logger]: Falha ao registrar log: {e}")


def read_log() -> str:
    """
    Lê todo o conteúdo do arquivo de log.
    Retorna uma string vazia se o arquivo não existir.
    """
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                # Lê o arquivo e inverte as linhas (mais novo primeiro)
                linhas = f.readlines()
                return "".join(reversed(linhas))
        else:
            return "Nenhum histórico de log encontrado."

    except Exception as e:
        print(f"ERRO [app_logger]: Falha ao ler log: {e}")
        return f"Erro ao ler o arquivo de log: {e}"


def clear_log() -> None:
    """
    Limpa o arquivo de log (trunca o arquivo).
    """
    try:
        # Abre em modo 'w' (write) para truncar (limpar) o arquivo
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            pass  # Apenas abrir e fechar em modo 'w' limpa o arquivo

        log_action("Histórico de logs limpo.")

    except Exception as e:
        print(f"ERRO [app_logger]: Falha ao limpar log: {e}")
        raise e  # Re-levanta o erro para o main.py
