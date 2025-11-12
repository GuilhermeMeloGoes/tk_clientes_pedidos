"""
Utils.py (Funções Utilitárias)

Contém funções auxiliares usadas em várias partes do aplicativo,
como centralização de janelas, configuração de temas e
lógica de análise de IA.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Tuple
import httpx  # Para chamadas de API (assíncrono)
import asyncio  # Para executar a chamada de API de forma assíncrona
import models  # Para buscar os dados dos pedidos
import db  # Para o `models` usar

# --- Constantes da API de IA (Ollama) ---
# O Ollama por padrão roda nesta porta.
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Prompt da IA (lido do README.md, mas deixamos uma cópia aqui
# caso o README não seja encontrado)
IA_PROMPT_DEFAULT = """
Com base nos dados dos últimos 5 pedidos fornecidos abaixo, atue como um assistente de negócios e forneça um breve resumo (em 3 ou 4 pontos) sobre os insights mais importantes.

Concentre-se em:
- Quais produtos parecem ser os mais populares?
- Qual é o ticket médio (valor médio por pedido) desses pedidos?
- Há algum padrão óbvio (ex: clientes recorrentes, itens comprados juntos)?

Seja breve e direto ao ponto.

--- DADOS DOS PEDIDOS ---

{dados_formatados_aqui}
"""


def center_window(window: tk.Toplevel, width_ratio: float = 0.5, height_ratio: float = 0.5):
    """
    Centraliza uma janela Toplevel na tela principal.

    :param window: A janela Toplevel a ser centralizada.
    :param width_ratio: (Opcional) Proporção da largura da tela (0.0 a 1.0).
    :param height_ratio: (Opcional) Proporção da altura da tela (0.0 a 1.0).
    """
    # Garante que as dimensões da janela sejam calculadas
    window.update_idletasks()

    # Tenta obter o master (janela principal) para centralizar
    master = window.master
    if master:
        screen_width = master.winfo_width()
        screen_height = master.winfo_height()
        master_x = master.winfo_x()
        master_y = master.winfo_y()
    else:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        master_x = 0
        master_y = 0

    # Pega as dimensões da janela Toplevel
    window_width = window.winfo_width()
    window_height = window.winfo_height()

    # Se a janela não tiver dimensão (ex: muito no início),
    # tenta estimar com base nas proporções.
    if window_width <= 1:
        window_width = int(screen_width * width_ratio)
    if window_height <= 1:
        window_height = int(screen_height * height_ratio)

    # Calcula a posição (x, y)
    x = master_x + (screen_width // 2) - (window_width // 2)
    y = master_y + (screen_height // 2) - (window_height // 2)

    # Define a geometria (posição)
    window.geometry(f"+{x}+{y}")


# =============================================================================
# === LÓGICA DE TEMAS (CLARO/ESCURO) ===
# =============================================================================

def setup_light_theme(style: ttk.Style):
    """Configura o estilo do ttk para um tema claro (padrão 'clam')."""

    try:
        style.theme_use('clam')
    except tk.TclError:
        print("INFO [utils.theme]: Tema 'clam' não disponível, usando 'default'.")
        style.theme_use('default')

    # Cores Claras
    bg_color = "#f0f0f0"
    fg_color = "#000000"
    base_color = "#ffffff"
    select_bg = "#b0e0e6"  # Azul claro
    select_fg = "#000000"

    # Configurações Globais
    style.configure(".",
                    background=bg_color,
                    foreground=fg_color,
                    fieldbackground=base_color,
                    font=("-size 10"))
    style.configure("TLabel", background=bg_color, foreground=fg_color)
    style.configure("TFrame", background=bg_color)

    # Botões
    style.configure("TButton",
                    background="#d9d9d9",
                    foreground=fg_color,
                    borderwidth=1,
                    padding="5 5 5 5")
    style.map("TButton",
              background=[('active', '#c0c0c0'), ('disabled', '#e0e0e0')],
              foreground=[('disabled', '#a0a0a0')])

    # Treeview
    style.configure("Treeview",
                    background=base_color,
                    fieldbackground=base_color,
                    foreground=fg_color)
    style.map("Treeview",
              background=[('selected', select_bg)],
              foreground=[('selected', select_fg)])

    style.configure("Treeview.Heading",
                    background="#d9d9d9",
                    foreground=fg_color,
                    font=("-size 10 -weight bold"),
                    padding=5)
    style.map("Treeview.Heading",
              background=[('active', '#c0c0c0')])

    # Entradas
    style.configure("TEntry",
                    fieldbackground=base_color,
                    foreground=fg_color,
                    insertcolor=fg_color)  # Cor do cursor
    style.configure("TSpinbox",
                    fieldbackground=base_color,
                    foreground=fg_color,
                    insertcolor=fg_color)
    style.map("TCombobox",
              fieldbackground=[('readonly', base_color)],
              foreground=[('readonly', fg_color)],
              selectbackground=[('readonly', base_color)],
              selectforeground=[('readonly', fg_color)])

    # Label Secundária
    style.configure("Secondary.TLabel", foreground="#555555")
    # Card do Dashboard
    style.configure("Card.TFrame", background=base_color)


def setup_dark_theme(style: ttk.Style):
    """Configura o estilo do ttk para um tema escuro."""

    try:
        style.theme_use('clam')
    except tk.TclError:
        print("INFO [utils.theme]: Tema 'clam' não disponível, usando 'default'.")
        style.theme_use('default')

    # Cores Escuras
    bg_color = "#2e2e2e"
    fg_color = "#d1d1d1"
    base_color = "#3c3c3c"
    select_bg = "#5a5a5a"  # Cinza médio
    select_fg = "#ffffff"

    # Configurações Globais
    style.configure(".",
                    background=bg_color,
                    foreground=fg_color,
                    fieldbackground=base_color,
                    font=("-size 10"))
    style.configure("TLabel", background=bg_color, foreground=fg_color)
    style.configure("TFrame", background=bg_color)

    # Botões
    style.configure("TButton",
                    background="#4f4f4f",
                    foreground=fg_color,
                    borderwidth=1,
                    padding="5 5 5 5")
    style.map("TButton",
              background=[('active', '#6a6a6a'), ('disabled', '#404040')],
              foreground=[('disabled', '#808080')])

    # Treeview
    style.configure("Treeview",
                    background=base_color,
                    fieldbackground=base_color,
                    foreground=fg_color)
    style.map("Treeview",
              background=[('selected', select_bg)],
              foreground=[('selected', select_fg)])

    style.configure("Treeview.Heading",
                    background="#4f4f4f",
                    foreground=fg_color,
                    font=("-size 10 -weight bold"),
                    padding=5)
    style.map("Treeview.Heading",
              background=[('active', '#6a6a6a')])

    # Entradas
    style.configure("TEntry",
                    fieldbackground=base_color,
                    foreground=fg_color,
                    insertcolor=fg_color)
    style.configure("TSpinbox",
                    fieldbackground=base_color,
                    foreground=fg_color,
                    insertcolor=fg_color)
    style.map("TCombobox",
              fieldbackground=[('readonly', base_color)],
              foreground=[('readonly', fg_color)],
              selectbackground=[('readonly', base_color)],
              selectforeground=[('readonly', fg_color)])

    # Label Secundária
    style.configure("Secondary.TLabel", foreground="#aaaaaa")
    # Card do Dashboard
    style.configure("Card.TFrame", background=base_color)


# =============================================================================
# === LÓGICA DE ANÁLISE IA (NOVO) ===
# =============================================================================

def _get_ia_prompt() -> str:
    """Lê o prompt do README.md, se falhar, usa o default."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
            # Busca o prompt dentro do bloco de código
            prompt_marker = "--- DADOS DOS PEDIDOS ---"
            if prompt_marker in content:
                # Pega tudo desde o início do arquivo até o marcador
                prompt = content.split(prompt_marker)[0]
                # Adiciona o marcador de formatação de volta
                prompt += "{dados_formatados_aqui}\n```"
                return prompt

        print("AVISO [utils.ia]: Não foi possível extrair o prompt do README.md, usando default.")
        return IA_PROMPT_DEFAULT

    except FileNotFoundError:
        print("AVISO [utils.ia]: README.md não encontrado, usando prompt default.")
        return IA_PROMPT_DEFAULT
    except Exception as e:
        print(f"ERRO [utils.ia]: Erro ao ler README.md: {e}")
        return IA_PROMPT_DEFAULT


def _formatar_dados_para_ia(pedidos_ids: List[int]) -> str:
    """
    Busca os detalhes dos pedidos no 'models' e formata
    um único string para enviar à IA.
    """
    dados_formatados = ""

    for i, pedido_id in enumerate(pedidos_ids):
        try:
            # Busca os detalhes (dicionários) do models
            pedido_info, itens_list = models.get_pedido_details(pedido_id)

            if not pedido_info:
                dados_formatados += f"\n--- Pedido {i + 1} (ID: {pedido_id}) ---\n"
                dados_formatados += "[Pedido não encontrado ou inválido]\n"
                continue

            # Formata o Pedido
            dados_formatados += f"\n--- Pedido {i + 1} (ID: {pedido_id}) ---\n"
            dados_formatados += f"Cliente: {pedido_info.get('cliente_nome')}\n"
            dados_formatados += f"Data: {pedido_info.get('data')}\n"

            # Formata os Itens
            dados_formatados += "Itens:\n"
            if not itens_list:
                dados_formatados += "- (Nenhum item encontrado)\n"
            else:
                for item in itens_list:
                    dados_formatados += (
                        f"- {item.get('produto')} "
                        f"(Qtd: {item.get('quantidade')}, "
                        f"Preço Unit: R$ {item.get('preco_unit', 0.0):.2f})\n"
                    )

            dados_formatados += f"Total do Pedido: R$ {pedido_info.get('total', 0.0):.2f}\n"

        except Exception as e:
            print(f"ERRO [utils._formatar_dados]: Falha ao buscar Pedido ID {pedido_id}: {e}")
            dados_formatados += f"\n--- Pedido {i + 1} (ID: {pedido_id}) ---\n"
            dados_formatados += f"[Erro ao processar este pedido: {e}]\n"

    return dados_formatados


async def _chamar_api_ollama(prompt_completo: str) -> str:
    """
    Chama a API do Ollama (local) de forma assíncrona.
    """
    # Payload para o Ollama
    payload = {
        "model": "phi3",  # Modelo padrão, pode ser "llama3", "phi3", etc.
        "prompt": prompt_completo,
        "stream": False  # Queremos a resposta completa, não streaming
    }

    # Timeout de 5 minutos (para IAs locais que podem demorar)
    timeout = httpx.Timeout(300.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            print("INFO [utils.ia]: Enviando requisição para o Ollama...")
            response = await client.post(OLLAMA_API_URL, json=payload)

            # Verifica se a requisição foi bem-sucedida
            response.raise_for_status()

            json_response = response.json()

            # Extrai a resposta
            if "response" in json_response:
                print("INFO [utils.ia]: Resposta recebida do Ollama.")
                return json_response["response"].strip()
            else:
                return f"Erro: Resposta inesperada da API:\n{json_response}"

        except httpx.ConnectError as e:
            print(f"ERRO [utils.ia]: Não foi possível conectar ao Ollama. {e}")
            return (
                "ERRO: Não foi possível conectar ao Ollama.\n\n"
                "Verifique se o Ollama está rodando localmente "
                f"em {OLLAMA_API_URL}"
            )
        except httpx.HTTPStatusError as e:
            print(f"ERRO [utils.ia]: Erro HTTP. Status: {e.response.status_code}")
            return f"ERRO: Falha na API. Status: {e.response.status_code}\n{e.response.text}"
        except Exception as e:
            print(f"ERRO [utils.ia]: Erro inesperado na chamada da API: {e}")
            return f"ERRO: Ocorreu um erro inesperado:\n{e}"


def analisar_pedidos_ia() -> str:
    """
    Função principal (síncrona) que o 'main.py' chama (em uma thread).

    1. Busca os IDs dos últimos pedidos.
    2. Formata os dados.
    3. Inicia o loop de eventos asyncio para chamar a API.
    4. Retorna a resposta (string) da IA.
    """
    try:
        # 1. Busca os IDs dos últimos 5 pedidos
        print("INFO [utils.ia]: Buscando últimos 5 pedidos...")
        # (O 'models' usa o 'db', que vai criar sua própria conexão)
        pedidos_ids = models.get_last_n_order_ids(n=5)

        if not pedidos_ids:
            return "Não há pedidos recentes para analisar."

        # 2. Formata os dados (buscando detalhes)
        print("INFO [utils.ia]: Formatando dados para IA...")
        dados_formatados = _formatar_dados_para_ia(pedidos_ids)

        # 3. Pega o prompt do README (ou o default)
        prompt_template = _get_ia_prompt()

        # 4. Cria o prompt completo
        prompt_completo = prompt_template.format(dados_formatados_aqui=dados_formatados)

        # print("DEBUG [utils.ia]: Prompt enviado:\n", prompt_completo) # (Descomentar para debug)

        # 5. Chama a função assíncrona (API)
        # Como estamos DENTRO de uma thread separada (criada no main.py),
        # é seguro criar um novo loop de eventos asyncio.
        print("INFO [utils.ia]: Iniciando loop asyncio para chamada da API...")
        resposta = asyncio.run(_chamar_api_ollama(prompt_completo))

        return resposta

    except Exception as e:
        print(f"ERRO [utils.analisar_pedidos_ia]: Falha no processo de análise: {e}")
        return f"Erro fatal ao tentar analisar os pedidos: {e}"
