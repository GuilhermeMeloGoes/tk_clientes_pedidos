"""
Views/Dashboard_View.py

Define o frame (tela) da aba Dashboard.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext  # Importa o widget de texto com rolagem
from typing import Callable, Dict, Any


class DashboardFrame(ttk.Frame):
    """
    Frame principal para a aba Dashboard.
    Exibe estatísticas rápidas, botão de atualização e análise de IA.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_refresh_callback: Callable[[], None],
                 on_analyze_callback: Callable[[], None]  # <-- NOVO
                 ):
        """
        Inicializa o frame do Dashboard.

        :param master: O widget pai (a aba do Notebook).
        :param on_refresh_callback: Callback para o botão 'Atualizar'.
        :param on_analyze_callback: Callback para o botão 'Analisar Pedidos'.
        """
        super().__init__(master, padding="20")  # Padding interno

        self.on_refresh = on_refresh_callback
        self.on_analyze = on_analyze_callback  # <-- NOVO

        # Variáveis de controle para os Labels
        self.total_clientes_var = tk.StringVar(value="...")
        self.pedidos_mes_var = tk.StringVar(value="...")
        self.ticket_medio_var = tk.StringVar(value="...")
        self.receita_mes_var = tk.StringVar(value="...")

        # Lista para guardar referências dos labels de valor (para o tema)
        self.value_labels = []

        # Cria os widgets
        self.create_widgets()

    def create_widgets(self):
        """Cria e posiciona os widgets no frame."""

        # --- Frame de Título e Atualização ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 25), anchor="n")  # Anchor 'n' (Norte/Topo)

        title_label = ttk.Label(header_frame, text="Dashboard", font=("-size 16 -weight bold"))
        title_label.pack(side="left")

        self.refresh_button = ttk.Button(header_frame, text="Atualizar Dados", command=self.on_refresh)
        self.refresh_button.pack(side="right")

        # --- Frame dos Cards de Estatísticas ---
        stats_frame = ttk.Frame(self)
        # Ocupa o espaço horizontal, mas não expande verticalmente
        stats_frame.pack(fill="x", expand=False, pady=(0, 10), anchor="n")

        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.columnconfigure(3, weight=1)

        # Cards
        card1 = self._create_stat_card(stats_frame, "Total de Clientes", self.total_clientes_var)
        card1.grid(row=0, column=0, padx=10, sticky="nsew")
        card2 = self._create_stat_card(stats_frame, "Pedidos (Mês Atual)", self.pedidos_mes_var)
        card2.grid(row=0, column=1, padx=10, sticky="nsew")
        card3 = self._create_stat_card(stats_frame, "Receita (Mês Atual)", self.receita_mes_var)
        card3.grid(row=0, column=2, padx=10, sticky="nsew")
        card4 = self._create_stat_card(stats_frame, "Ticket Médio (Mês Atual)", self.ticket_medio_var)
        card4.grid(row=0, column=3, padx=10, sticky="nsew")

        # --- Frame da Análise de IA (NOVO) ---
        analysis_frame = ttk.LabelFrame(self, text="Análise de IA (Últimos 5 Pedidos)", padding="15")
        # Ocupa o resto do espaço (fill e expand=True)
        analysis_frame.pack(fill="both", expand=True, pady=(10, 0))

        analysis_frame.rowconfigure(1, weight=1)  # Linha do Texto (expande)
        analysis_frame.columnconfigure(0, weight=1)  # Coluna do Texto (expande)

        # Botão de Ação (Linha 0)
        self.analysis_button = ttk.Button(analysis_frame, text="Analisar Pedidos (Ollama/phi3)",
                                          command=self.on_analyze)
        self.analysis_button.grid(row=0, column=0, sticky="e", pady=(0, 10))  # Alinhado à direita

        # Área de Texto (Linha 1)
        self.analysis_text_area = scrolledtext.ScrolledText(
            analysis_frame,
            wrap=tk.WORD,
            font=("Consolas", 10, "normal"),
            state="disabled",
            height=10,  # Altura inicial
            bg="#ffffff",  # Padrão claro
            fg="#000000"
        )
        self.analysis_text_area.grid(row=1, column=0, sticky="nsew")

    def _create_stat_card(self, master: tk.Widget, title: str,
                          textvariable: tk.StringVar) -> ttk.Frame:
        """ Helper para criar um "card" de estatística. """
        card_frame = ttk.Frame(master,
                               padding="15 20 15 20",
                               style="Card.TFrame",
                               borderwidth=1,
                               relief="solid")

        title_label = ttk.Label(card_frame, text=title,
                                font=("-size 10 -weight bold"))
        title_label.pack(pady=(0, 10))

        # (Usamos ttk.Label, mas a cor é controlada pelo 'foreground')
        value_label = ttk.Label(card_frame,
                                textvariable=textvariable,
                                font=("-size 20 -weight bold"),
                                style="Value.TLabel")  # Estilo customizado
        value_label.pack(pady=10)

        # Guarda a referência para atualizar o tema
        self.value_labels.append(value_label)

        style = ttk.Style()
        style.configure("Card.TFrame", background="white")
        style.configure("Value.TLabel",
                        background="white",
                        foreground="#333333")  # Cor inicial clara

        return card_frame

    def update_stats(self, stats: Dict[str, Any]):
        """ Atualiza os StringVars com os novos dados vindos do 'main.py'. """
        total_clientes = stats.get("total_clientes", 0)
        self.total_clientes_var.set(f"{total_clientes}")

        pedidos_mes = stats.get("pedidos_mes_atual", 0)
        self.pedidos_mes_var.set(f"{pedidos_mes}")

        receita_mes = stats.get("receita_total_mes", 0.0)
        self.receita_mes_var.set(f"R$ {receita_mes:.2f}")

        ticket_medio = stats.get("ticket_medio_mes_atual", 0.0)
        self.ticket_medio_var.set(f"R$ {ticket_medio:.2f}")

    def set_loading_state(self, is_loading: bool):
        """ Desativa o botão de atualizar enquanto os dados estão sendo carregados. """
        if is_loading:
            self.refresh_button.config(state="disabled", text="Atualizando...")
            self.total_clientes_var.set("...")
            self.pedidos_mes_var.set("...")
            self.receita_mes_var.set("...")
            self.ticket_medio_var.set("...")
        else:
            self.refresh_button.config(state="normal", text="Atualizar Dados")

    def set_analysis_state(self, is_analyzing: bool):
        """ Desativa o botão de análise e limpa o texto. """
        if is_analyzing:
            self.analysis_button.config(state="disabled", text="Analisando...")
            self.analysis_text_area.config(state="normal")
            self.analysis_text_area.delete("1.0", tk.END)
            self.analysis_text_area.insert("1.0", "Aguarde, analisando os últimos pedidos com a IA...")
            self.analysis_text_area.config(state="disabled")
        else:
            self.analysis_button.config(state="normal", text="Analisar Pedidos (Ollama/phi3)")

    def set_analysis_result(self, result: str):
        """ Exibe o resultado da análise (ou erro) na área de texto. """
        self.analysis_text_area.config(state="normal")
        self.analysis_text_area.delete("1.0", tk.END)
        self.analysis_text_area.insert("1.0", result)
        self.analysis_text_area.config(state="disabled")

    def update_theme(self, is_dark: bool):
        """
        Atualiza as cores dos widgets (ScrolledText e Labels dos Cards)
        quando o tema é trocado.
        """
        if is_dark:
            # Cores do Tema Escuro
            text_bg = "#2e2e2e"
            text_fg = "#d1d1d1"
            card_val_bg = "#3c3c3c"  # Fundo do card
            card_val_fg = "#d1d1d1"  # Texto do valor
        else:
            # Cores do Tema Claro
            text_bg = "#ffffff"
            text_fg = "#000000"
            card_val_bg = "#ffffff"  # Fundo do card
            card_val_fg = "#333333"  # Texto do valor

        # Atualiza o ScrolledText (que não é ttk)
        self.analysis_text_area.config(background=text_bg, foreground=text_fg)

        # Atualiza os Labels de Valor (que são ttk, mas precisam de reconfiguração
        # do 'style' para o foreground e background)
        style = ttk.Style()
        style.configure("Value.TLabel",
                        background=card_val_bg,
                        foreground=card_val_fg)
