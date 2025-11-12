"""
Views/Relatorios_View.py

Define o frame (tela) da aba Relatórios.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List, Tuple
import utils  # Importa o utils
from tkcalendar import DateEntry  # Importa o seletor de data
import datetime


# =============================================================================
# === FRAME DA LISTA DE RELATÓRIOS (COM FILTROS) ===
# =============================================================================

class RelatoriosViewFrame(ttk.Frame):
    """
    Frame principal para a aba Relatórios.
    Contém a Treeview, filtros e botões de exportação.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_search_callback: Callable[[str, str, str], None],
                 on_clear_filters_callback: Callable[[], None],
                 on_export_csv_callback: Callable[[List[Tuple]], None],
                 on_export_pdf_callback: Callable[[List[Tuple]], None],
                 clientes_combobox_data: List[Tuple]  # (id, nome)
                 ):
        """
        Inicializa o frame de Relatórios.

        :param master: O widget pai (a aba do Notebook).
        :param on_search_callback: Callback para o botão 'Buscar'.
        :param on_clear_filters_callback: Callback para o botão 'Limpar Filtros'.
        :param on_export_csv_callback: Callback para o botão 'Exportar CSV'.
        :param on_export_pdf_callback: Callback para o botão 'Exportar PDF'.
        :param clientes_combobox_data: Lista de (id, nome) para o filtro.
        """
        super().__init__(master, padding="0")

        self.on_search = on_search_callback
        self.on_clear_filters = on_clear_filters_callback
        self.on_export_csv = on_export_csv_callback
        self.on_export_pdf = on_export_pdf_callback

        # Mapeia os dados do combobox
        # Adiciona um "Todos os Clientes" no início
        self.clientes_map = {nome: id for id, nome in clientes_combobox_data}
        self.clientes_nomes = ["Todos os Clientes"] + [nome for id, nome in clientes_combobox_data]
        self.clientes_map["Todos os Clientes"] = ""  # ID vazio para "Todos"

        # Estado interno para armazenar os dados atuais da lista
        self.current_data_list: List[Tuple] = []

        # Variáveis de controle
        self.cliente_filter_var = tk.StringVar(value="Todos os Clientes")

        # Cria os widgets
        self.create_widgets()

    def create_widgets(self):
        """Cria e posiciona os widgets no frame."""

        # --- Frame de Ações e Filtros (Topo) ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 10))

        # --- Sub-frame para Filtros (Linha 1) ---
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(fill="x", pady=(0, 8))

        # Filtro Data Início
        ttk.Label(filter_frame, text="Data Início:").pack(side="left", padx=(0, 5))
        self.date_start_entry = DateEntry(filter_frame, width=12, background='darkblue',
                                          foreground='white', borderwidth=2,
                                          date_pattern='dd/mm/yyyy',
                                          locale='pt_BR')
        self.date_start_entry.pack(side="left", padx=5)
        self.date_start_entry.set_date(None)

        # Filtro Data Fim
        ttk.Label(filter_frame, text="Data Fim:").pack(side="left", padx=(15, 5))
        self.date_end_entry = DateEntry(filter_frame, width=12, background='darkblue',
                                        foreground='white', borderwidth=2,
                                        date_pattern='dd/mm/yyyy',
                                        locale='pt_BR')
        self.date_end_entry.pack(side="left", padx=5)
        self.date_end_entry.set_date(None)

        # Filtro Cliente (Combobox)
        ttk.Label(filter_frame, text="Cliente:").pack(side="left", padx=(15, 5))
        self.cliente_combobox = ttk.Combobox(
            filter_frame,
            textvariable=self.cliente_filter_var,
            values=self.clientes_nomes,
            state="readonly",
            width=30
        )
        self.cliente_combobox.pack(side="left", padx=5, fill="x", expand=True)

        # --- Sub-frame para Botões (Linha 2) ---
        action_frame = ttk.Frame(top_frame)
        action_frame.pack(fill="x", pady=(5, 0))

        # Botões de Filtro
        self.search_button = ttk.Button(action_frame, text="Buscar", command=self._on_search_click)
        self.search_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(action_frame, text="Limpar", command=self._on_clear_filters_click)
        self.clear_button.pack(side="left", padx=5)

        # Botões de Exportação (alinhados à direita)
        self.export_pdf_button = ttk.Button(action_frame, text="Exportar PDF (Lista)",
                                            command=self._on_export_pdf_click)
        self.export_pdf_button.pack(side="right", padx=5)

        self.export_csv_button = ttk.Button(action_frame, text="Exportar CSV (Lista)",
                                            command=self._on_export_csv_click)
        self.export_csv_button.pack(side="right", padx=5)

        # --- Frame da Treeview (Centro) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        # Colunas da Treeview
        columns = ("id", "data", "cliente", "itens", "total")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configuração das Colunas
        self.tree.heading("id", text="ID Pedido")
        self.tree.column("id", width=80, stretch=False, anchor="center")

        self.tree.heading("data", text="Data")
        self.tree.column("data", width=100, anchor="center")

        self.tree.heading("cliente", text="Cliente")
        self.tree.column("cliente", width=250)

        self.tree.heading("itens", text="Itens (Qtd)")
        self.tree.column("itens", width=300)  # Coluna larga para os itens

        self.tree.heading("total", text="Total (R$)")
        self.tree.column("total", width=100, anchor="e")  # 'e' (east) = alinhado à direita

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Posicionamento (Grid dentro do tree_frame)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

    def _on_search_click(self, event=None):
        """Callback do botão de busca (ou Enter)."""

        # Pega o ID do cliente selecionado no combobox
        cliente_nome = self.cliente_filter_var.get()
        cliente_id = self.clientes_map.get(cliente_nome, "")  # "" para "Todos"

        # Converte as datas para 'YYYY-MM-DD' ou string vazia
        try:
            date_start = self.date_start_entry.get_date().strftime("%Y-%m-%d")
        except AttributeError:
            date_start = ""

        try:
            date_end = self.date_end_entry.get_date().strftime("%Y-%m-%d")
        except AttributeError:
            date_end = ""

        # Chama o callback do main.py
        self.on_search(str(cliente_id), date_start, date_end)

    def _on_clear_filters_click(self):
        """Callback para o botão 'Limpar Filtros'."""
        self.clear_filters()
        # Chama o callback do main.py (sem argumentos)
        self.on_clear_filters()

    def _check_data_before_export(self) -> bool:
        """Verifica se há dados na lista antes de exportar."""
        if not self.current_data_list:
            messagebox.showinfo("Nenhum Dado",
                                "Não há dados na lista para exportar. "
                                "Por favor, clique em 'Buscar' primeiro.",
                                parent=self)
            return False
        return True

    def _on_export_csv_click(self):
        """Callback do botão 'Exportar CSV'."""
        if not self._check_data_before_export():
            return

        self.on_export_csv(self.current_data_list)

    def _on_export_pdf_click(self):
        """Callback do botão 'Exportar PDF'."""
        if not self._check_data_before_export():
            return

        self.on_export_pdf(self.current_data_list)

    def refresh_data(self, relatorios_list: List[Tuple]):
        """
        Limpa a Treeview e a recarrega com novos dados.

        :param relatorios_list: Uma lista de tuplas, onde cada tupla
                               (id, data, cliente_nome, itens_str, total).
        """
        # Salva os dados localmente (para exportação)
        self.current_data_list = relatorios_list

        # Limpa todos os itens existentes
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere os novos dados
        for row in relatorios_list:
            # (id, data, cliente, itens, total)

            # Formata o total para R$
            total_formatado = f"{row[4]:.2f}"

            # Formata a string de itens (ex: "Produto A (2); Produto B (1)")
            # Substitui as vírgulas por "; "
            itens_str = row[3].replace(",", "; ")

            # Recria a tupla com os valores formatados
            values_formatados = (
                row[0],  # id
                row[1],  # data
                row[2],  # cliente
                itens_str,  # itens formatados
                total_formatado  # total
            )
            self.tree.insert("", tk.END, values=values_formatados)

    def clear_filters(self):
        """Limpa os campos de filtro na interface."""
        self.cliente_filter_var.set("Todos os Clientes")
        self.date_start_entry.set_date(None)
        self.date_end_entry.set_date(None)
        self.date_end_entry.set_date(None)
