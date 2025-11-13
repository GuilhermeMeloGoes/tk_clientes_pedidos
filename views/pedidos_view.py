"""
Views/Pedidos_View.py

Define o frame (tela) da aba Pedidos e o Toplevel (popup)
para criar um novo pedido.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List, Tuple
import utils # Importa o utils
from tkcalendar import DateEntry # Importa o seletor de data
import datetime

# =============================================================================
# === FRAME DA LISTA DE PEDIDOS (COM FILTROS) ===
# =============================================================================

class PedidosViewFrame(ttk.Frame):
    """
    Frame principal para a aba Pedidos.
    Contém a Treeview, filtros e botões de ação.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_new_callback: Callable[[], None], # <-- NOVO
                 on_delete_callback: Callable[[int], None],
                 on_search_callback: Callable[[str, str, str], None],
                 on_clear_filters_callback: Callable[[], None],
                 on_export_csv_callback: Callable[[int], None],
                 on_export_pdf_callback: Callable[[int], None]
                ):
        """
        Inicializa o frame de Pedidos.

        :param master: O widget pai (a aba do Notebook).
        :param on_new_callback: Callback para o botão 'Novo Pedido'.
        :param on_delete_callback: Callback para o botão 'Excluir'.
        :param on_search_callback: Callback para o botão 'Buscar'.
        :param on_clear_filters_callback: Callback para o botão 'Limpar Filtros'.
        :param on_export_csv_callback: Callback para 'Exportar CSV'.
        :param on_export_pdf_callback: Callback para 'Exportar PDF'.
        """
        super().__init__(master, padding="0")

        # Callbacks
        self.on_new = on_new_callback # <-- NOVO
        self.on_delete = on_delete_callback
        self.on_search = on_search_callback
        self.on_clear_filters = on_clear_filters_callback
        self.on_export_csv = on_export_csv_callback
        self.on_export_pdf = on_export_pdf_callback

        # Variáveis de controle
        self.search_var = tk.StringVar()

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

        # Filtro Busca
        ttk.Label(filter_frame, text="Buscar (Nome/Email):").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        # Binda o <Return> (Enter) para a busca
        self.search_entry.bind("<Return>", self._on_search_click)

        # Filtro Data Início
        ttk.Label(filter_frame, text="Data Início:").pack(side="left", padx=(15, 5))
        self.date_start_entry = DateEntry(filter_frame, width=12, background='darkblue',
                                          foreground='white', borderwidth=2,
                                          date_pattern='dd/mm/yyyy',
                                          locale='pt_BR') # pt_BR para formato DD/MM/YYYY
        self.date_start_entry.pack(side="left", padx=5)
        self.date_start_entry.set_date(None) # Começa vazio

        # Filtro Data Fim
        ttk.Label(filter_frame, text="Data Fim:").pack(side="left", padx=(15, 5))
        self.date_end_entry = DateEntry(filter_frame, width=12, background='darkblue',
                                        foreground='white', borderwidth=2,
                                        date_pattern='dd/mm/yyyy',
                                        locale='pt_BR')
        self.date_end_entry.pack(side="left", padx=5)
        self.date_end_entry.set_date(None) # Começa vazio

        # --- Sub-frame para Botões (Linha 2) ---
        action_frame = ttk.Frame(top_frame)
        action_frame.pack(fill="x", pady=(5, 0))

        # Botões de Filtro
        self.search_button = ttk.Button(action_frame, text="Buscar", command=self._on_search_click)
        self.search_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(action_frame, text="Limpar", command=self._on_clear_filters_click)
        self.clear_button.pack(side="left", padx=5)

        # Botões de Ação (alinhados à direita)
        self.delete_button = ttk.Button(action_frame, text="Excluir Selecionado", command=self._on_delete_click)
        self.delete_button.pack(side="right", padx=5)

        self.export_pdf_button = ttk.Button(action_frame, text="Exportar PDF", command=self._on_export_pdf_click)
        self.export_pdf_button.pack(side="right", padx=5)

        self.export_csv_button = ttk.Button(action_frame, text="Exportar CSV", command=self._on_export_csv_click)
        self.export_csv_button.pack(side="right", padx=5)

        # Botão Novo Pedido (NOVO)
        self.new_button = ttk.Button(action_frame, text="Novo Pedido", command=self.on_new)
        self.new_button.pack(side="right", padx=5)


        # --- Frame da Treeview (Centro) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        # Colunas da Treeview
        columns = ("id", "data", "cliente", "total")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configuração das Colunas
        self.tree.heading("id", text="ID Pedido")
        self.tree.column("id", width=80, stretch=False, anchor="center")

        self.tree.heading("data", text="Data")
        self.tree.column("data", width=120, anchor="center")

        self.tree.heading("cliente", text="Cliente")
        self.tree.column("cliente", width=400) # Coluna larga

        self.tree.heading("total", text="Total (R$)")
        self.tree.column("total", width=120, anchor="e") # 'e' (east) = alinhado à direita

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

    def _get_selected_pedido_id(self) -> Optional[int]:
        """Helper para pegar o ID do item selecionado na Treeview."""
        try:
            selected_item = self.tree.selection()[0] # Pega o primeiro (e único) item selecionado
            pedido_id = self.tree.item(selected_item, "values")[0]
            return int(pedido_id)
        except IndexError:
            messagebox.showwarning("Nenhum Pedido Selecionado",
                                   "Por favor, selecione um pedido na lista primeiro.",
                                   parent=self)
            return None
        except (ValueError, TypeError):
            messagebox.showerror("Erro de Seleção",
                                 "Não foi possível identificar o ID do pedido selecionado.",
                                 parent=self)
            return None

    def _on_search_click(self, event=None):
        """Callback do botão de busca (ou Enter)."""
        search_term = self.search_var.get().strip()

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
        self.on_search(search_term, date_start, date_end)

    def _on_clear_filters_click(self):
        """Callback para o botão 'Limpar Filtros'."""
        self.search_var.set("")
        self.date_start_entry.set_date(None)
        self.date_end_entry.set_date(None)

        # Chama o callback do main.py (sem argumentos)
        self.on_clear_filters()

    def _on_delete_click(self):
        """Callback do botão 'Excluir'."""
        pedido_id = self._get_selected_pedido_id()
        if pedido_id is None:
            return

        if messagebox.askyesno("Confirmar Exclusão",
                               f"Tem certeza que deseja excluir o Pedido ID {pedido_id}?\n\n"
                               "Todos os itens deste pedido também serão excluídos.",
                               parent=self, icon="warning"):

            # Chama o callback do main.py
            self.on_delete(pedido_id)

    def _on_export_csv_click(self):
        """Callback do botão 'Exportar CSV'."""
        pedido_id = self._get_selected_pedido_id()
        if pedido_id is None:
            return

        # Chama o callback do main.py
        self.on_export_csv(pedido_id)

    def _on_export_pdf_click(self):
        """Callback do botão 'Exportar PDF'."""
        pedido_id = self._get_selected_pedido_id()
        if pedido_id is None:
            return

        # Chama o callback do main.py
        self.on_export_pdf(pedido_id)


    def refresh_data(self, pedidos_list: List[Tuple]):
        """
        Limpa a Treeview e a recarrega com novos dados.

        :param pedidos_list: Uma lista de tuplas, onde cada tupla
                               (id, data, cliente_nome, total).
        """
        # Limpa todos os itens existentes
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere os novos dados
        for row in pedidos_list:
            # row = (id, data, cliente, total)

            # Formata o total para R$ 123.45
            total_formatado = f"{row[3]:.2f}"

            # Recria a tupla com o valor formatado
            values_formatados = (row[0], row[1], row[2], total_formatado)

            self.tree.insert("", tk.END, values=values_formatados)

    def clear_filters(self):
        """Limpa os campos de filtro na interface."""
        self.search_var.set("")
        self.date_start_entry.set_date(None)
        self.date_end_entry.set_date(None)


# =============================================================================
# === FORMULÁRIO DE PEDIDO (POPUP TOPLEVEL) ===
# =============================================================================

class PedidoForm(tk.Toplevel):
    """
    Janela Toplevel (popup) para criar um novo Pedido.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_save_callback: Callable[[Dict[str, Any], List[Dict[str, Any]]], None],
                 on_cancel_callback: Callable[[], None],
                 on_dirty_callback: Callable[[tk.Toplevel], None],
                 clientes_combobox_data: List[Tuple] # Lista de (id, nome)
                ):
        """
        Inicializa o formulário.

        :param master: O widget pai (a janela principal 'App').
        :param on_save_callback: Função a ser chamada ao salvar.
        :param on_cancel_callback: Função a ser chamada ao fechar/cancelar.
        :param on_dirty_callback: Função a ser chamada quando dados mudam.
        :param clientes_combobox_data: Lista de clientes para o Combobox.
        """
        super().__init__(master)

        self.on_save = on_save_callback
        self.on_cancel = on_cancel_callback
        self.on_dirty = on_dirty_callback

        self.title("Novo Pedido")
        self.transient(master) # Mantém sobre a janela principal
        self.grab_set()        # Modal

        # Mapeia os dados do combobox
        self.clientes_map = {nome: id for id, nome in clientes_combobox_data}
        self.clientes_nomes = [nome for id, nome in clientes_combobox_data]

        # Estado interno
        self.is_dirty = False # Rastreia alterações não salvas
        self.total_pedido_var = tk.DoubleVar(value=0.0)

        # Variáveis de controle para os campos
        self.cliente_var = tk.StringVar()
        self.data_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))

        # Cria os widgets
        self.create_widgets()

        # Centraliza a janela
        utils.center_window(self, width_ratio=0.6, height_ratio=0.7)

        # Intercepta o 'X' da janela
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

    def create_widgets(self):
        """Cria e posiciona os widgets no formulário."""

        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill="both", expand=True)

        # --- Frame Superior (Cliente e Data) ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 15))

        # Cliente (Combobox)
        ttk.Label(top_frame, text="Cliente:*").pack(side="left", padx=(0, 5))
        self.cliente_combobox = ttk.Combobox(
            top_frame,
            textvariable=self.cliente_var,
            values=self.clientes_nomes,
            state="readonly",
            width=40
        )
        self.cliente_combobox.pack(side="left", padx=5, fill="x", expand=True)
        self.cliente_combobox.bind("<<ComboboxSelected>>", self._set_dirty)

        # Data (Entry)
        ttk.Label(top_frame, text="Data (AAAA-MM-DD):*").pack(side="left", padx=(15, 5))
        self.data_entry = ttk.Entry(top_frame, textvariable=self.data_var, width=12)
        self.data_entry.pack(side="left", padx=5)
        self.data_var.trace_add("write", self._set_dirty)

        # --- Frame Central (Itens do Pedido) ---
        items_frame = ttk.LabelFrame(main_frame, text="Itens do Pedido", padding="10")
        items_frame.pack(fill="both", expand=True, pady=10)

        items_frame.rowconfigure(1, weight=1) # Linha da Treeview (expande)
        items_frame.columnconfigure(0, weight=1) # Coluna da Treeview (expande)

        # --- Sub-frame para Adicionar Itens (Linha 0) ---
        add_item_frame = ttk.Frame(items_frame)
        add_item_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Configuração flexível do grid
        add_item_frame.columnconfigure(1, weight=2) # Produto
        add_item_frame.columnconfigure(3, weight=1) # Qtd
        add_item_frame.columnconfigure(5, weight=1) # Preço

        ttk.Label(add_item_frame, text="Produto:").grid(row=0, column=0, padx=5, sticky="w")
        self.item_produto_var = tk.StringVar()
        self.item_produto_entry = ttk.Entry(add_item_frame, textvariable=self.item_produto_var, width=30)
        self.item_produto_entry.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(add_item_frame, text="Qtd:").grid(row=0, column=2, padx=5, sticky="w")
        self.item_qtd_var = tk.IntVar(value=1)
        self.item_qtd_spinbox = ttk.Spinbox(add_item_frame, textvariable=self.item_qtd_var, from_=1, to=999, width=5)
        self.item_qtd_spinbox.grid(row=0, column=3, padx=5, sticky="ew")

        ttk.Label(add_item_frame, text="Preço Unit (R$):").grid(row=0, column=4, padx=5, sticky="w")
        self.item_preco_var = tk.DoubleVar()
        self.item_preco_entry = ttk.Entry(add_item_frame, textvariable=self.item_preco_var, width=10)
        self.item_preco_entry.grid(row=0, column=5, padx=5, sticky="ew")

        # Binda o <Return> (Enter) no último campo (Preço)
        self.item_preco_entry.bind("<Return>", self._on_add_item_click)

        # Botão Adicionar Item
        self.add_item_button = ttk.Button(add_item_frame, text="Adicionar Item", command=self._on_add_item_click)
        self.add_item_button.grid(row=0, column=6, padx=10, sticky="e")

        # --- Treeview dos Itens (Linha 1) ---
        tree_frame = ttk.Frame(items_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        columns = ("produto", "quantidade", "preco_unit", "subtotal")
        self.items_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        self.items_tree.heading("produto", text="Produto")
        self.items_tree.column("produto", width=300)
        self.items_tree.heading("quantidade", text="Qtd")
        self.items_tree.column("quantidade", width=80, anchor="center")
        self.items_tree.heading("preco_unit", text="Preço Unit. (R$)")
        self.items_tree.column("preco_unit", width=120, anchor="e")
        self.items_tree.heading("subtotal", text="Subtotal (R$)")
        self.items_tree.column("subtotal", width=120, anchor="e")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)

        self.items_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Botão Remover Item (Linha 2)
        self.remove_item_button = ttk.Button(items_frame, text="Remover Item Selecionado", command=self._on_remove_item_click)
        self.remove_item_button.grid(row=2, column=0, sticky="e", pady=(10, 0))

        # --- Frame Inferior (Total e Botões) ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(15, 0))

        # Total
        ttk.Label(bottom_frame, text="Total do Pedido:", font=("-size 12 -weight bold")).pack(side="left")
        self.total_label = ttk.Label(bottom_frame,
                                     textvariable=self.total_pedido_var,
                                     font=("-size 12 -weight bold"))
        self.total_label.pack(side="left", padx=10)

        # Botões Salvar/Cancelar (alinhados à direita)
        self.cancel_button = ttk.Button(bottom_frame, text="Cancelar", command=self._on_close_window)
        self.cancel_button.pack(side="right", padx=5)

        self.save_button = ttk.Button(bottom_frame, text="Salvar Pedido", command=self._on_save_click)
        self.save_button.pack(side="right", padx=5)

    def _set_dirty(self, *args):
        """
        Marca o formulário como 'sujo' (dados não salvos)
        e notifica o 'main.py' (Controlador).
        """
        if not self.is_dirty:
            self.is_dirty = True
            # Notifica o main.py (Controlador)
            self.on_dirty(self)
            print("INFO [PedidoForm]: Formulário marcado como 'dirty'.")

    def _on_add_item_click(self, event=None):
        """Valida e adiciona um item à Treeview de itens."""

        produto = self.item_produto_var.get().strip()

        try:
            quantidade = self.item_qtd_var.get()
            if quantidade <= 0:
                raise ValueError("Quantidade deve ser positiva")
        except (tk.TclError, ValueError):
            messagebox.showwarning("Valor Inválido",
                                   "A 'Quantidade' deve ser um número inteiro positivo.",
                                   parent=self)
            self.item_qtd_spinbox.focus_set()
            return

        try:
            preco_unit = self.item_preco_var.get()
            if preco_unit <= 0:
                 raise ValueError("Preço deve ser positivo")
        except (tk.TclError, ValueError):
            messagebox.showwarning("Valor Inválido",
                                   "O 'Preço Unitário' deve ser um número positivo (ex: 10.50).",
                                   parent=self)
            self.item_preco_entry.focus_set()
            return

        if not produto:
            messagebox.showwarning("Campo Obrigatório",
                                   "O campo 'Produto' é obrigatório.",
                                   parent=self)
            self.item_produto_entry.focus_set()
            return

        # Calcula subtotal
        subtotal = quantidade * preco_unit

        # Insere na Treeview
        values = (
            produto,
            quantidade,
            f"{preco_unit:.2f}",
            f"{subtotal:.2f}"
        )
        self.items_tree.insert("", tk.END, values=values)

        # Marca o form como 'dirty'
        self._set_dirty()

        # Limpa os campos de entrada
        self.item_produto_var.set("")
        self.item_qtd_var.set(1)
        self.item_preco_var.set(0.0)

        # Atualiza o total
        self._update_total()

        # Foca no primeiro campo (Produto)
        self.item_produto_entry.focus_set()

    def _on_remove_item_click(self):
        """Remove um item selecionado da Treeview de itens."""
        try:
            selected_item = self.items_tree.selection()[0]
        except IndexError:
            messagebox.showwarning("Nenhum Item Selecionado",
                                   "Por favor, selecione um item na lista para remover.",
                                   parent=self)
            return

        self.items_tree.delete(selected_item)

        # Marca o form como 'dirty'
        self._set_dirty()

        # Atualiza o total
        self._update_total()

    def _update_total(self):
        """Recalcula o valor total do pedido com base nos itens da Treeview."""
        total = 0.0

        for item_id in self.items_tree.get_children():
            values = self.items_tree.item(item_id, "values")
            try:
                # O subtotal (R$ 123.45) é o índice 3
                subtotal_str = values[3]
                total += float(subtotal_str)
            except (IndexError, ValueError):
                print(f"AVISO [PedidoForm]: Ignorando linha inválida na Treeview: {values}")

        self.total_pedido_var.set(f"{total:.2f}")

    def _validate_form(self) -> Optional[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Valida o formulário principal (Cliente, Data) e
        coleta os dados dos itens da Treeview.

        :return: (pedido_data, itens_data) ou None se a validação falhar.
        """

        # 1. Valida Cliente
        cliente_nome = self.cliente_var.get()
        if not cliente_nome:
            messagebox.showwarning("Campo Obrigatório",
                                   "Por favor, selecione um 'Cliente'.",
                                   parent=self)
            self.cliente_combobox.focus_set()
            return None

        cliente_id = self.clientes_map.get(cliente_nome)
        if cliente_id is None: # Segurança (não deve acontecer)
             messagebox.showerror("Erro Interno",
                                  "Erro ao processar o ID do cliente.",
                                  parent=self)
             return None

        # 2. Valida Data
        data_str = self.data_var.get().strip()
        try:
            # Tenta converter para data (valida o formato YYYY-MM-DD)
            datetime.date.fromisoformat(data_str)
        except ValueError:
            messagebox.showwarning("Formato Inválido",
                                   "A 'Data' deve estar no formato AAAA-MM-DD (ex: 2025-11-10).",
                                   parent=self)
            self.data_entry.focus_set()
            return None

        # 3. Valida Total (e coleta itens)
        total_pedido = 0.0
        itens_data_list = []

        if not self.items_tree.get_children():
            messagebox.showwarning("Nenhum Item",
                                   "O pedido deve ter pelo menos um item.",
                                   parent=self)
            self.item_produto_entry.focus_set()
            return None

        for item_id in self.items_tree.get_children():
            values = self.items_tree.item(item_id, "values")
            # values = (produto, quantidade, preco_unit, subtotal)
            try:
                produto = values[0]
                quantidade = int(values[1])
                preco_unit = float(values[2])

                itens_data_list.append({
                    "produto": produto,
                    "quantidade": quantidade,
                    "preco_unit": preco_unit
                })
                total_pedido += (quantidade * preco_unit)

            except (IndexError, ValueError, TypeError):
                 messagebox.showerror("Erro Interno",
                                      f"Erro ao processar os itens do pedido (linha: {values}).",
                                      parent=self)
                 return None

        # Confirma se o total calculado bate com o label (segurança)
        self._update_total()
        label_total = float(self.total_pedido_var.get())
        if abs(total_pedido - label_total) > 0.001:
             messagebox.showerror("Erro de Cálculo",
                                  "O total calculado (R$ {total_pedido:.2f}) não bate "
                                  "com o total exibido (R$ {label_total:.2f}).",
                                  parent=self)
             return None

        # 4. Prepara os dados para o 'main.py'
        pedido_data = {
            "cliente_id": cliente_id,
            "data": data_str,
            "total": total_pedido
        }

        return (pedido_data, itens_data_list)


    def _on_save_click(self):
        """Callback do botão 'Salvar'."""

        # 1. Valida o formulário e coleta os dados
        validated_data = self._validate_form()

        if validated_data is None:
            return # Validação falhou

        pedido_data, itens_data_list = validated_data

        try:
            # 2. Chama o callback do 'main.py' (que chama o 'models')
            self.on_save(pedido_data, itens_data_list)

            # 3. Se o 'on_save' (models) não deu erro, fecha
            self.is_dirty = False # Marcar como "não sujo" antes de fechar
            self.destroy() # Fecha o Toplevel
            self.on_cancel() # Notifica o 'main'

        except Exception as e:
            # Se o 'main.save_pedido' (models) levantar o erro
            # (ex: falha na transação), o 'except' dele lá no 'main'
            # vai mostrar a messagebox.
            # O 'raise e' dele vai fazer este 'except' ser ativado,
            # impedindo que o form seja fechado.
            print(f"INFO [PedidoForm.on_save]: Ocorreu um erro ao salvar (esperado), formulário não será fechado.")

    def _on_close_window(self):
        """
        Chamado ao clicar no 'X' ou no botão 'Cancelar'.
        Verifica se há dados não salvos ('dirty').
        """
        if self.is_dirty:
            if not messagebox.askyesno("Descartar Alterações?",
                                         "Você tem alterações não salvas. "
                                         "Deseja fechar e descartar?",
                                         parent=self, icon="warning"):
                return # Não fecha

        # Se não estiver 'dirty' ou se o usuário confirmou
        self.is_dirty = False
        self.destroy()
        self.on_cancel()