import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List, Tuple
import utils  # Importa o utils
from tkcalendar import DateEntry  # Importa o seletor de data
import datetime


# =============================================================================
# === FRAME DA LISTA DE PEDIDOS (COM FILTROS) ===
# =============================================================================

class PedidosViewFrame(ttk.Frame):
    """
    Frame principal para listar e gerenciar pedidos.
    Contém a Treeview, botões de ação, busca e filtros de data.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_delete_callback: Callable[[int], None],
                 on_search_callback: Callable[[str, str, str], None],
                 on_clear_filters_callback: Callable[[], None],
                 on_export_csv_callback: Callable[[int], None],
                 on_export_pdf_callback: Callable[[int], None]
                 ):
        """
        Inicializa o frame da lista de pedidos.

        :param master: O widget pai (ex: um Notebook ou a janela principal).
        :param on_delete_callback: Callback para o botão 'Excluir'.
        :param on_search_callback: Callback para o botão 'Buscar'.
        :param on_clear_filters_callback: Callback para o botão 'Limpar Filtros'.
        :param on_export_csv_callback: Callback para o botão 'Exportar CSV'.
        :param on_export_pdf_callback: Callback para o botão 'Exportar PDF'.
        """
        super().__init__(master, padding="0")

        self.on_delete = on_delete_callback
        self.on_search = on_search_callback
        self.on_clear_filters = on_clear_filters_callback
        self.on_export_csv = on_export_csv_callback
        self.on_export_pdf = on_export_pdf_callback

        # Variável de controle para a busca
        self.search_var = tk.StringVar()

        # Cria os widgets
        self.create_widgets()

    def create_widgets(self):
        """Cria e posiciona os widgets no frame."""

        # --- Frame de Ações e Filtros (Topo) ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 10))

        # --- Sub-frame para Filtros de Data (Linha 1) ---
        date_filter_frame = ttk.Frame(top_frame)
        date_filter_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(date_filter_frame, text="Data Início:").pack(side="left", padx=(0, 5))
        self.date_start_entry = DateEntry(date_filter_frame, width=12, background='darkblue',
                                          foreground='white', borderwidth=2,
                                          date_pattern='dd/mm/yyyy',  # Formato de exibição
                                          locale='pt_BR')
        self.date_start_entry.pack(side="left", padx=5)
        self.date_start_entry.set_date(None)  # Limpa o campo

        ttk.Label(date_filter_frame, text="Data Fim:").pack(side="left", padx=(15, 5))
        self.date_end_entry = DateEntry(date_filter_frame, width=12, background='darkblue',
                                        foreground='white', borderwidth=2,
                                        date_pattern='dd/mm/yyyy',  # Formato de exibição
                                        locale='pt_BR')
        self.date_end_entry.pack(side="left", padx=5)
        self.date_end_entry.set_date(None)  # Limpa o campo

        # --- Sub-frame para Busca e Ações (Linha 2) ---
        search_action_frame = ttk.Frame(top_frame)
        search_action_frame.pack(fill="x", pady=(5, 0))

        # Busca por Cliente
        ttk.Label(search_action_frame, text="Buscar Cliente:").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(search_action_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.search_button = ttk.Button(search_action_frame, text="Buscar", command=self._on_search_click)
        self.search_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(search_action_frame, text="Limpar", command=self._on_clear_filters_click)
        self.clear_button.pack(side="left", padx=5)

        # Bind <Return> (Enter) nos campos
        self.search_entry.bind("<Return>", self._on_search_click)
        self.date_start_entry.bind("<Return>", self._on_search_click)
        self.date_end_entry.bind("<Return>", self._on_search_click)

        # Botões de Ação (Exportação e Exclusão)
        self.delete_button = ttk.Button(search_action_frame, text="Excluir Pedido", command=self._on_delete_click)
        self.delete_button.pack(side="right", padx=(15, 0))  # Mais margem

        self.export_pdf_button = ttk.Button(search_action_frame, text="Exportar PDF", command=self._on_export_pdf_click)
        self.export_pdf_button.pack(side="right", padx=5)

        self.export_csv_button = ttk.Button(search_action_frame, text="Exportar CSV", command=self._on_export_csv_click)
        self.export_csv_button.pack(side="right", padx=5)

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
        self.tree.column("data", width=100, anchor="center")

        self.tree.heading("cliente", text="Cliente")
        self.tree.column("cliente", width=300)

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

    def _get_selected_item_data(self) -> Optional[Dict[str, Any]]:
        """
        Retorna os dados do item selecionado na Treeview.
        Retorna um dicionário ou None se nada for selecionado.
        """
        selected_iid = self.tree.focus()  # IID (Internal ID)
        if not selected_iid:
            return None

        item_values = self.tree.item(selected_iid, "values")
        if not item_values:
            return None

        # Mapeia os valores de volta para um dicionário
        data = {
            "id": int(item_values[0]),
            "data": item_values[1],
            "cliente": item_values[2],
            "total": float(item_values[3])  # Total é um float
        }
        return data

    def _get_selected_item_id(self) -> Optional[int]:
        """ Helper que retorna apenas o ID do item selecionado. """
        selected_data = self._get_selected_item_data()
        if selected_data:
            return selected_data.get("id")
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
        self.clear_filters()
        # Chama o callback do main.py
        self.on_clear_filters()

    def _on_delete_click(self):
        """Callback do botão 'Excluir'."""
        selected_data = self._get_selected_item_data()

        if not selected_data:
            messagebox.showinfo("Nenhum Pedido Selecionado",
                                "Por favor, selecione um pedido na lista para excluir.",
                                parent=self)
            return

        # Confirmação de exclusão
        if messagebox.askyesno("Confirmar Exclusão",
                               f"Tem certeza que deseja excluir o Pedido ID {selected_data['id']}?\n\n"
                               f"Cliente: {selected_data['cliente']}\n"
                               f"Data: {selected_data['data']}\n\n"
                               "Todos os itens deste pedido também serão excluídos.",
                               parent=self):
            self.on_delete(selected_data['id'])

    def _on_export_csv_click(self):
        """Callback do botão 'Exportar CSV'."""
        selected_id = self._get_selected_item_id()
        if not selected_id:
            messagebox.showinfo("Nenhum Pedido Selecionado",
                                "Por favor, selecione um pedido na lista para exportar.",
                                parent=self)
            return

        self.on_export_csv(selected_id)

    def _on_export_pdf_click(self):
        """Callback do botão 'Exportar PDF'."""
        selected_id = self._get_selected_item_id()
        if not selected_id:
            messagebox.showinfo("Nenhum Pedido Selecionado",
                                "Por favor, selecione um pedido na lista para exportar.",
                                parent=self)
            return

        self.on_export_pdf(selected_id)

    def refresh_data(self, pedidos_list: List[Tuple]):
        """
        Limpa a Treeview e a recarrega com novos dados.

        :param pedidos_list: Uma lista de tuplas, onde cada tupla
                             corresponde aos dados de um pedido
                             (id, data, cliente_nome, total).
        """
        # Limpa todos os itens existentes
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere os novos dados
        for pedido_data in pedidos_list:
            # (id, data, cliente, total)
            # Formata o total para R$
            total_formatado = f"{pedido_data[3]:.2f}"

            # Recria a tupla com o total formatado
            values_formatados = (
                pedido_data[0],  # id
                pedido_data[1],  # data
                pedido_data[2],  # cliente
                total_formatado  # total
            )
            self.tree.insert("", tk.END, values=values_formatados)

    def clear_filters(self):
        """Limpa os campos de filtro na interface."""
        self.search_var.set("")
        self.date_start_entry.set_date(None)
        self.date_end_entry.set_date(None)


# =============================================================================
# === CLASSE DO FORMULÁRIO DE PEDIDO ===
# =============================================================================

class PedidoForm(tk.Toplevel):
    """
    Janela Toplevel modal para criar um novo pedido.
    """

    def __init__(self,
                 master: tk.Tk,
                 on_save_callback: Callable[[Dict, List], None],
                 on_cancel_callback: Callable[[], None],
                 clientes_combobox_data: List[Tuple]
                 ):
        """
        Inicializa o formulário de pedido.

        :param master: A janela principal (root).
        :param on_save_callback: Função a ser chamada ao salvar.
        :param on_cancel_callback: Função a ser chamada ao cancelar ou fechar.
        :param clientes_combobox_data: Lista de tuplas (id, nome) de clientes.
        """
        super().__init__(master)

        # Configurações do Toplevel
        self.master = master
        self.on_save_callback = on_save_callback
        self.on_cancel_callback = on_cancel_callback

        # Dados para o Combobox de Clientes
        self.clientes_map = {nome: id for id, nome in clientes_combobox_data}
        self.clientes_nomes = [nome for id, nome in clientes_combobox_data]

        # Estado interno
        self.itens_pedido_list = []  # Lista de dicionários

        # Variáveis de controle do Tkinter
        self.cliente_var = tk.StringVar()
        self.data_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        self.total_var = tk.DoubleVar(value=0.0)

        # Variáveis de controle para "Adicionar Item"
        self.item_produto_var = tk.StringVar()
        self.item_qtd_var = tk.IntVar(value=1)
        self.item_preco_var = tk.DoubleVar()

        self.title("Novo Pedido")

        # Cria os widgets
        self.create_widgets()

        # Flag para verificar se o usuário alterou algum dado
        self.is_dirty = False
        # Adiciona traces
        self.cliente_var.trace_add("write", self._set_dirty)
        self.data_var.trace_add("write", self._set_dirty)

        # Configuração de modal
        self.transient(master)
        self.grab_set()

        # Intercepta o botão de fechar (o "X")
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Centraliza a janela (usa o utils)
        utils.center_window(self)

        # Foca no primeiro campo de entrada
        self.cliente_combobox.focus_set()

    def create_widgets(self):
        """Cria e posiciona os widgets no formulário."""

        # Frame principal com padding
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill="both", expand=True)

        # --- Seção de Informações do Pedido (Topo) ---
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=(0, 15))

        # Cliente
        ttk.Label(info_frame, text="Cliente:*").pack(side="left", padx=(0, 5))
        self.cliente_combobox = ttk.Combobox(
            info_frame,
            textvariable=self.cliente_var,
            values=self.clientes_nomes,
            state="readonly"  # Impede digitação
        )
        self.cliente_combobox.pack(side="left", padx=5, fill="x", expand=True)

        # Data (não editável, apenas exibição)
        ttk.Label(info_frame, text="Data:").pack(side="left", padx=(15, 5))
        self.data_entry = ttk.Entry(info_frame, textvariable=self.data_var, width=12, state="disabled")
        self.data_entry.pack(side="left", padx=5)

        # --- Seção Adicionar Item (Meio) ---
        add_item_frame = ttk.LabelFrame(main_frame, text="Adicionar Item", padding="10")
        add_item_frame.pack(fill="x", pady=(0, 15))

        # Configuração do grid (4 colunas para campos, 1 para botão)
        add_item_frame.columnconfigure(0, weight=3)  # Produto
        add_item_frame.columnconfigure(1, weight=1)  # Qtd
        add_item_frame.columnconfigure(2, weight=1)  # Preço
        add_item_frame.columnconfigure(3, minsize=40)  # Espaço
        add_item_frame.columnconfigure(4, weight=1)  # Botão

        # Labels
        ttk.Label(add_item_frame, text="Produto:").grid(row=0, column=0, sticky="w")
        ttk.Label(add_item_frame, text="Qtd:").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(add_item_frame, text="Preço Unit (R$):").grid(row=0, column=2, sticky="w", padx=5)

        # Entries
        self.item_produto_entry = ttk.Entry(add_item_frame, textvariable=self.item_produto_var)
        self.item_produto_entry.grid(row=1, column=0, sticky="ew")

        self.item_qtd_spinbox = ttk.Spinbox(add_item_frame, from_=1, to=999, textvariable=self.item_qtd_var, width=6)
        self.item_qtd_spinbox.grid(row=1, column=1, sticky="w", padx=5)

        self.item_preco_entry = ttk.Entry(add_item_frame, textvariable=self.item_preco_var, width=10)
        self.item_preco_entry.grid(row=1, column=2, sticky="w", padx=5)

        # Botão Adicionar Item
        self.add_item_button = ttk.Button(add_item_frame, text="Adicionar", command=self._on_add_item)
        self.add_item_button.grid(row=1, column=4, sticky="e", padx=5)

        # Bind <Return> (Enter) para adicionar item
        self.item_produto_entry.bind("<Return>", self._on_add_item)
        self.item_qtd_spinbox.bind("<Return>", self._on_add_item)
        self.item_preco_entry.bind("<Return>", self._on_add_item)

        # --- Seção Itens do Pedido (Treeview) ---
        itens_frame = ttk.Frame(main_frame)
        itens_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Colunas da Treeview
        columns = ("produto", "quantidade", "preco_unit", "subtotal")

        self.tree = ttk.Treeview(itens_frame, columns=columns, show="headings", height=8)

        # Configuração das Colunas
        self.tree.heading("produto", text="Produto")
        self.tree.column("produto", width=250)

        self.tree.heading("quantidade", text="Qtd")
        self.tree.column("quantidade", width=50, anchor="center")

        self.tree.heading("preco_unit", text="Preço Unit.")
        self.tree.column("preco_unit", width=100, anchor="e")

        self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("subtotal", width=100, anchor="e")

        # Scrollbar Y
        scrollbar_y = ttk.Scrollbar(itens_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        # Posicionamento (Grid dentro do itens_frame)
        itens_frame.grid_rowconfigure(0, weight=1)
        itens_frame.grid_columnconfigure(0, weight=1)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        # Botão Remover Item (abaixo da tree)
        self.remove_item_button = ttk.Button(itens_frame, text="Remover Item Selecionado", command=self._on_remove_item)
        self.remove_item_button.grid(row=1, column=0, sticky="w", pady=(5, 0))

        # --- Seção Total e Botões (Rodapé) ---
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill="x", pady=(10, 0))

        # Label do Total
        ttk.Label(footer_frame, text="Total do Pedido (R$):").pack(side="left")
        self.total_label = ttk.Label(footer_frame,
                                     textvariable=self.total_var,
                                     font=("-weight bold"),
                                     width=12,
                                     anchor="e")
        self.total_label.pack(side="left", padx=5)

        # Botões Salvar/Cancelar
        self.cancel_button = ttk.Button(footer_frame, text="Cancelar", command=self.on_cancel)
        self.cancel_button.pack(side="right", padx=5)

        self.save_button = ttk.Button(footer_frame, text="Salvar Pedido", command=self.on_save)
        self.save_button.pack(side="right", padx=5)

    def _set_dirty(self, *args):
        """Marca o formulário como 'modificado'."""
        self.is_dirty = True

    def _validate_add_item(self) -> (bool, dict):
        """Valida os campos de 'Adicionar Item'."""
        produto = self.item_produto_var.get().strip()

        try:
            quantidade = self.item_qtd_var.get()
        except tk.TclError:
            messagebox.showwarning("Valor Inválido", "A quantidade deve ser um número inteiro.", parent=self)
            self.item_qtd_spinbox.focus_set()
            return False, {}

        try:
            preco_unit = self.item_preco_var.get()
        except tk.TclError:
            messagebox.showwarning("Valor Inválido", "O preço deve ser um número (ex: 10.50).", parent=self)
            self.item_preco_entry.focus_set()
            return False, {}

        # Validações lógicas
        if not produto:
            messagebox.showwarning("Campo Obrigatório", "O 'Produto' é obrigatório.", parent=self)
            self.item_produto_entry.focus_set()
            return False, {}

        if quantidade <= 0:
            messagebox.showwarning("Valor Inválido", "A 'Quantidade' deve ser maior que zero.", parent=self)
            self.item_qtd_spinbox.focus_set()
            return False, {}

        if preco_unit <= 0:
            messagebox.showwarning("Valor Inválido", "O 'Preço Unitário' deve ser maior que zero.", parent=self)
            self.item_preco_entry.focus_set()
            return False, {}

        # Dados validados
        item_data = {
            "produto": produto,
            "quantidade": quantidade,
            "preco_unit": preco_unit
        }
        return True, item_data

    def _on_add_item(self, event=None):
        """Callback do botão 'Adicionar' ou Enter."""
        is_valid, item_data = self._validate_add_item()

        if not is_valid:
            return

        # 1. Adiciona na lista de estado interna
        self.itens_pedido_list.append(item_data)

        # 2. Adiciona na Treeview
        subtotal = item_data["quantidade"] * item_data["preco_unit"]

        # Formata para exibição
        preco_f = f"{item_data['preco_unit']:.2f}"
        subtotal_f = f"{subtotal:.2f}"

        self.tree.insert("", tk.END,
                         values=(item_data["produto"],
                                 item_data["quantidade"],
                                 preco_f,
                                 subtotal_f)
                         )

        # 3. Atualiza o total
        self._update_total()

        # 4. Limpa os campos e foca no produto
        self.item_produto_var.set("")
        self.item_qtd_var.set(1)
        self.item_preco_var.set(0.0)
        self.item_produto_entry.focus_set()

        # 5. Marca o form como "dirty"
        self._set_dirty()

    def _on_remove_item(self):
        """Callback do botão 'Remover Item Selecionado'."""
        selected_iid = self.tree.focus()  # IID (Internal ID)
        if not selected_iid:
            messagebox.showinfo("Nenhum Item Selecionado",
                                "Por favor, selecione um item na lista para remover.",
                                parent=self)
            return

        # A treeview não armazena os dados originais (ex: R$ 10.50 vira "10.50").
        # Precisamos encontrar o item na nossa lista interna (itens_pedido_list)
        # pelo índice da treeview.

        try:
            # Pega o índice do item na Treeview (0, 1, 2...)
            index = self.tree.index(selected_iid)

            # Remove da lista de estado
            removed_item = self.itens_pedido_list.pop(index)

            # Remove da Treeview
            self.tree.delete(selected_iid)

            # Atualiza o total
            self._update_total()

            # Marca o form como "dirty"
            self._set_dirty()

        except IndexError:
            # Isso não deve acontecer se a tree e a lista estiverem em sincronia
            print(f"ERRO [PedidoForm._on_remove_item]: Índice {index} não encontrado na lista de itens.")
        except Exception as e:
            print(f"ERRO [PedidoForm._on_remove_item]: {e}")

    def _update_total(self):
        """Calcula e atualiza o total do pedido com base na lista interna."""
        total = 0.0
        for item in self.itens_pedido_list:
            total += item["quantidade"] * item["preco_unit"]

        self.total_var.set(f"{total:.2f}")

    def _validate_save(self) -> (bool, dict):
        """Valida o formulário antes de salvar."""

        # 1. Valida Cliente
        cliente_nome = self.cliente_var.get()
        if not cliente_nome:
            messagebox.showwarning("Campo Obrigatório", "O 'Cliente' é obrigatório.", parent=self)
            self.cliente_combobox.focus_set()
            return False, {}

        # 2. Valida se há itens
        if not self.itens_pedido_list:
            messagebox.showwarning("Pedido Vazio", "Você deve adicionar pelo menos um item ao pedido.", parent=self)
            self.item_produto_entry.focus_set()
            return False, {}

        # 3. Pega os dados validados
        try:
            cliente_id = self.clientes_map[cliente_nome]
        except KeyError:
            # Isso não deve acontecer se o combobox for 'readonly'
            messagebox.showerror("Erro Interno", f"Cliente '{cliente_nome}' não encontrado no mapa de clientes.",
                                 parent=self)
            return False, {}

        # Dados do Pedido (sem os itens)
        pedido_data = {
            "cliente_id": cliente_id,
            "data": self.data_var.get(),
            "total": self.total_var.get()
        }

        return True, pedido_data

    def on_save(self):
        """Callback do botão 'Salvar'."""
        is_valid, pedido_data = self._validate_save()

        if not is_valid:
            return  # Para a execução se a validação falhar

        # Chama o callback externo (main.py)
        # Passa os dados do pedido E a lista de itens
        try:
            self.on_save_callback(pedido_data, self.itens_pedido_list)
            self.is_dirty = False  # Marca como "limpo" antes de fechar
            self.destroy()  # Fecha a janela

        except Exception as e:
            # Se o 'main.save_pedido' levantar o erro (ex: falha na transação),
            # o 'except' dele lá no main vai mostrar a messagebox,
            # e o 'raise e' dele vai fazer este 'except' ser ativado,
            # impedindo que o form seja fechado.

            # Limpamos os comentários com erro de sintaxe
            print(f"INFO [PedidoForm.on_save]: Ocorreu um erro ao salvar (esperado), formulário não será fechado.")

    def on_cancel(self):
        """Callback do botão 'Cancelar' ou do 'X' da janela."""

        # Verifica se há dados não salvos (se o cliente mudou ou itens foram add/remov)
        if self.is_dirty:
            if not messagebox.askyesno("Descartar Pedido?",
                                       "Você tem um pedido em andamento que não foi salvo. "
                                       "Deseja fechar e descartar?",
                                       parent=self):
                return  # Não fecha

        self.on_cancel_callback()
        self.destroy()