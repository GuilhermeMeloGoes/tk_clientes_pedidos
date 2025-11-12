"""
Views/Historico_View.py

Define o frame (tela) da aba Histórico.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext  # Importa o widget de texto com rolagem
from typing import Callable, Optional


class HistoricoViewFrame(ttk.Frame):
    """
    Frame principal para a aba Histórico.
    Exibe os logs do arquivo 'app.log' em um widget Text.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_refresh_callback: Callable[[], None],
                 on_clear_callback: Callable[[], None]
                 ):
        """
        Inicializa o frame do Histórico.

        :param master: O widget pai (a aba do Notebook).
        :param on_refresh_callback: Callback para o botão 'Atualizar'.
        :param on_clear_callback: Callback para o botão 'Limpar Histórico'.
        """
        super().__init__(master, padding="0")  # Padding 0, a aba já tem

        self.on_refresh = on_refresh_callback
        self.on_clear = on_clear_callback

        # Cria os widgets
        self.create_widgets()

    def create_widgets(self):
        """Cria e posiciona os widgets no frame."""

        # --- Frame de Ações (Topo) ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 10))

        # Título
        title_label = ttk.Label(top_frame, text="Histórico de Ações (logs/app.log)", font=("-weight bold"))
        title_label.pack(side="left")

        # Botões (lado direito)
        self.clear_button = ttk.Button(top_frame, text="Limpar Histórico", command=self.on_clear)
        self.clear_button.pack(side="right", padx=5)

        self.refresh_button = ttk.Button(top_frame, text="Atualizar", command=self.on_refresh)
        self.refresh_button.pack(side="right", padx=5)

        # --- Widget de Texto (Centro) ---
        # Usamos ScrolledText para ter a barra de rolagem automaticamente
        self.log_text_area = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,  # Quebra de linha por palavra
            font=("Consolas", 10, "normal"),  # Fonte monoespaçada
            state="disabled",  # Começa como "somente leitura"
            bg="#ffffff",
            fg="#000000"
        )
        self.log_text_area.pack(fill="both", expand=True)

    def set_log_content(self, log_content: str):
        """
        Atualiza o conteúdo do widget Text com o log.
        """
        # 1. Habilita a escrita
        self.log_text_area.config(state="normal")

        # 2. Limpa o conteúdo antigo
        self.log_text_area.delete("1.0", tk.END)

        # 3. Insere o novo conteúdo
        self.log_text_area.insert("1.0", log_content)

        # 4. Desabilita a escrita (volta a ser somente leitura)
        self.log_text_area.config(state="disabled")

    def set_loading_state(self, is_loading: bool):
        """
        Desativa os botões enquanto os dados
        estão sendo carregados ou limpos.
        """
        if is_loading:
            self.refresh_button.config(state="disabled", text="Aguarde...")
            self.clear_button.config(state="disabled")
        else:
            self.refresh_button.config(state="normal", text="Atualizar")
            self.clear_button.config(state="normal")

    def update_theme(self, is_dark: bool):
        """
        Atualiza as cores do widget Text (que não é ttk)
        quando o tema é trocado.
        """
        if is_dark:
            # Cores do Tema Escuro
            bg_color = "#2e2e2e"
            fg_color = "#d1d1d1"
        else:
            # Cores do Tema Claro
            bg_color = "#ffffff"
            fg_color = "#000000"

        self.log_text_area.config(background=bg_color, foreground=fg_color)
