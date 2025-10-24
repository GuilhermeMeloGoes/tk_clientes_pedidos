import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

# Importa as validações
try:
    import utils
except ImportError:
    logging.warning("Módulo 'utils.py' não encontrado. Validações locais serão usadas.")
    utils = None

log = logging.getLogger(__name__)


class PedidoListView(ttk.Frame):
    """
    View principal para listar, buscar e gerenciar Pedidos.
    Usa callbacks para se comunicar com o controlador (main.py).
    """

    def __init__(self, parent):
        super().__init__(parent)

        # Callbacks (serão definidos pelo controlador via set_callbacks)
        self.on_search = None
        self.on_refresh = None
        self.on_add = None
        self.on_edit = None
        self.on_delete = None

        self._setup_widgets()

    def set_callbacks(self, on_search, on_refresh, on_add, on_edit, on_delete):
        """Define as funções de callback do controlador."""
        self.on_search = on_search
        self.on_refresh = on_refresh
        self.on_add = on_add
        self.on_edit = on_edit
        self.on_delete = on_delete

    def _setup_widgets(self):
        # Frame de busca e botões
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', pady=5, padx=5)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        search_button = ttk.Button(top_frame, text="Buscar", command=self._on_search_click)
        search_button.pack(side='left', padx=5)

        self.refresh_button = ttk.Button(top_frame, text="Atualizar Lista", command=self._on_refresh_click)
        self.refresh_button.pack(side='left', padx=5)

        add_button = ttk.Button(top_frame, text="Novo Pedido", command=self._on_add_click)
        add_button.pack(side='right', padx=5)

        self.edit_button = ttk.Button(top_frame, text="Editar Pedido", state='disabled', command=self._on_edit_click)
        self.edit_button.pack(side='right', padx=5)

        self.delete_button = ttk.Button(top_frame, text="Excluir Pedido", state='disabled',
                                        command=self._on_delete_click)
        self.delete_button.pack(side='right')

        # Bind <Return> (Enter) na barra de busca para acionar a busca
        search_entry.bind('<Return>', self._on_search_click)

        # --- Treeview para listar pedidos ---
        columns = ('id', 'cliente_nome', 'data', 'total')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')

        # Define cabeçalhos
        self.tree.heading('id', text='ID Pedido')
        self.tree.heading('cliente_nome', text='Cliente')
        self.tree.heading('data', text='Data')
        self.tree.heading('total', text='Total (R$)')

        # Define largura das colunas
        self.tree.column('id', width=80, anchor='center')
        self.tree.column('cliente_nome', width=300)
        self.tree.column('data', width=120, anchor='center')
        self.tree.column('total', width=120, anchor='e')  # 'e' (east) para alinhar à direita

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Binds de seleção
        self.tree.bind('<<TreeviewSelect>>', self._on_item_select)
        self.tree.bind('<Double-1>', self._on_double_click)

    def _on_item_select(self, event=None):
        """Habilita botões 'Editar' e 'Excluir' quando um item é selecionado."""
        if self.tree.selection():
            self.edit_button.config(state='normal')
            self.delete_button.config(state='normal')
        else:
            self.edit_button.config(state='disabled')
            self.delete_button.config(state='disabled')

    def _get_selected_id(self):
        """Retorna o ID do pedido selecionado no Treeview."""
        try:
            selected_item = self.tree.selection()[0]
            item_data = self.tree.item(selected_item)
            return item_data['values'][0]
        except IndexError:
            log.warning("Tentativa de ação (editar/excluir) sem item selecionado.")
            return None

    def _on_search_click(self, event=None):
        """Callback para o botão 'Buscar'."""
        if self.on_search:
            term = self.search_var.get()
            self.on_search(term)

    def _on_refresh_click(self):
        """Callback para o botão 'Atualizar Lista'."""
        if self.on_refresh:
            self.search_var.set("")  # Limpa a busca
            self.on_refresh()  # Chama o callback sem termo de busca

    def _on_add_click(self):
        """Callback para o botão 'Novo Pedido'."""
        if self.on_add:
            self.on_add()

    def _on_edit_click(self):
        """Callback para o botão 'Editar Pedido'."""
        selected_id = self._get_selected_id()
        if selected_id and self.on_edit:
            self.on_edit(selected_id)

    def _on_double_click(self, event):
        """Callback para clique duplo (aciona edição)."""
        if self.tree.identify_region(event.x, event.y) == "cell":
            self._on_edit_click()

    def _on_delete_click(self):
        """Callback para o botão 'Excluir Pedido'."""
        selected_id = self._get_selected_id()
        if selected_id and self.on_delete:
            self.on_delete(selected_id)

    def refresh_treeview(self, data):
        """Limpa e recarrega o Treeview com novos dados."""
        # Limpa a tabela
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Insere novos dados
        # Espera dados no formato [(id, nome_cliente, data, total), ...]
        for row in data:
            # Formata o total para R$
            try:
                total_formatado = f"{float(row[3]):.2f}"
            except (ValueError, TypeError):
                total_formatado = "0.00"

            # Cria a tupla final com o total formatado
            values = (row[0], row[1], row[2], total_formatado)
            self.tree.insert('', 'end', values=values)

        # Limpa a seleção após recarregar
        self._on_item_select()

    def show_confirm(self, title, message):
        """Exibe um popup de confirmação (usado pelo controlador)."""
        return messagebox.askyesno(title, message, parent=self)


# --- Formulário de Pedido (Janela Toplevel) ---

class PedidoFormWindow(tk.Toplevel):
    """
    Janela Toplevel para cadastrar ou editar um Pedido.
    Modos: 'new', 'edit', 'view'
    """

    def __init__(self, parent, mode='new', on_save=None, pedido_data=None, all_clients_list=None):
        super().__init__(parent)
        self.transient(parent)
        self.resizable(False, False)

        self.mode = mode
        self.on_save_callback = on_save
        self.pedido_data = pedido_data if pedido_data else {}
        self.all_clients_list = all_clients_list if all_clients_list else []

        # Rastreia alterações nos dados
        self.is_dirty = tk.BooleanVar(value=False)
        # Rastreia alterações *apenas* na lista de itens (para recálculo)
        self.itens_changed = tk.BooleanVar(value=False)

        self.itens_tree_data = {}  # Dicionário para guardar itens (key=ID do Treeview)
        self.item_counter = 0  # Contador para IDs únicos no Treeview

        self._setup_window_title_and_mode()
        self._setup_vars()
        self._setup_widgets()
        self._load_data()
        self._configure_states()

        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # Inicia o rastreamento de 'dirty' (exceto para o combobox, que é tratado no _load_data)
        self.data_var.trace_add("write", self._mark_as_dirty)
        self.itens_changed.trace_add("write", self._mark_as_dirty)

    def _setup_window_title_and_mode(self):
        """Define o título e se a janela é somente leitura."""
        if self.mode == 'new':
            self.title("Novo Pedido")
            self.is_readonly = False
        elif self.mode == 'edit':
            self.title(f"Editar Pedido #{self.pedido_data.get('id', '')}")
            self.is_readonly = False
        elif self.mode == 'view':
            self.title(f"Detalhes do Pedido #{self.pedido_data.get('id', '')}")
            self.is_readonly = True
        else:
            self.title("Pedido")
            self.is_readonly = True

    def _setup_vars(self):
        """Inicializa as StringVars e outras variáveis de controle."""
        self.cliente_var = tk.StringVar()
        self.data_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.total_var = tk.StringVar(value="R$ 0.00")

        # Mapeamento para o Combobox
        # Lista de nomes de clientes (para exibição)
        self.cliente_nomes = [cliente[1] for cliente in self.all_clients_list]
        # Dicionário para converter Nome -> ID
        self.cliente_nome_to_id = {nome: cid for cid, nome in self.all_clients_list}
        # Dicionário para converter ID -> Nome
        self.cliente_id_to_nome = {cid: nome for cid, nome in self.all_clients_list}

    def _setup_widgets(self):
        """Cria todos os componentes da interface."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)

        # --- Frame Superior (Cliente e Data) ---
        info_frame = ttk.Labelframe(main_frame, text="Informações do Pedido")
        info_frame.pack(fill='x', expand=True, pady=5)

        ttk.Label(info_frame, text="Cliente:").grid(row=0, column=0, sticky='w', padx=10, pady=10)
        self.cliente_combo = ttk.Combobox(
            info_frame,
            textvariable=self.cliente_var,
            values=self.cliente_nomes,
            width=40
        )
        self.cliente_combo.grid(row=0, column=1, sticky='we', padx=10, pady=10)
        # Bind para o 'dirty' flag (só queremos marcar se a seleção *mudar* do original)
        self.cliente_combo.bind('<<ComboboxSelected>>', self._mark_as_dirty)

        ttk.Label(info_frame, text="Data:").grid(row=1, column=0, sticky='w', padx=10, pady=10)
        self.data_entry = ttk.Entry(info_frame, textvariable=self.data_var, width=15)
        self.data_entry.grid(row=1, column=1, sticky='w', padx=10, pady=10)

        # --- Frame de Itens (Formulário de Adicionar) ---
        self.itens_add_frame = ttk.Labelframe(main_frame, text="Adicionar Item")
        self.itens_add_frame.pack(fill='x', expand=True, pady=10)

        # Labels
        ttk.Label(self.itens_add_frame, text="Produto:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(self.itens_add_frame, text="Qtd:").grid(row=0, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(self.itens_add_frame, text="Preço Unit.:").grid(row=0, column=2, sticky='w', padx=5, pady=5)

        # Entradas
        self.item_produto_var = tk.StringVar()
        self.item_qtd_var = tk.StringVar()
        self.item_preco_var = tk.StringVar()

        self.item_produto_entry = ttk.Entry(self.itens_add_frame, textvariable=self.item_produto_var, width=30)
        self.item_produto_entry.grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.item_qtd_entry = ttk.Entry(self.itens_add_frame, textvariable=self.item_qtd_var, width=8)
        self.item_qtd_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        self.item_preco_entry = ttk.Entry(self.itens_add_frame, textvariable=self.item_preco_var, width=12)
        self.item_preco_entry.grid(row=1, column=2, sticky='w', padx=5, pady=5)

        # Botões de Item
        self.add_item_button = ttk.Button(self.itens_add_frame, text="Adicionar", command=self._adicionar_item)
        self.add_item_button.grid(row=1, column=3, sticky='e', padx=10, pady=5)

        self.remove_item_button = ttk.Button(self.itens_add_frame, text="Remover Selecionado",
                                             command=self._remover_item, state='disabled')
        self.remove_item_button.grid(row=2, column=3, sticky='e', padx=10, pady=5)

        # Configura a expansão da coluna do produto
        self.itens_add_frame.grid_columnconfigure(0, weight=1)

        # --- Treeview de Itens ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True, pady=5)

        columns = ('produto', 'qtd', 'preco_unit', 'subtotal')
        self.itens_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse', height=5)

        self.itens_tree.heading('produto', text='Produto')
        self.itens_tree.heading('qtd', text='Qtd')
        self.itens_tree.heading('preco_unit', text='Preço Unit.')
        self.itens_tree.heading('subtotal', text='Subtotal')

        self.itens_tree.column('produto', width=250)
        self.itens_tree.column('qtd', width=50, anchor='center')
        self.itens_tree.column('preco_unit', width=100, anchor='e')
        self.itens_tree.column('subtotal', width=100, anchor='e')

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.itens_tree.yview)
        self.itens_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.itens_tree.pack(fill='both', expand=True)

        self.itens_tree.bind('<<TreeviewSelect>>', self._on_item_select)

        # --- Total e Botões ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill='x', expand=True, pady=(10, 0))

        # Label de Total
        total_label_frame = ttk.Frame(bottom_frame, borderwidth=2, relief="sunken")
        total_label_frame.pack(side='left', padx=5, pady=5)
        ttk.Label(total_label_frame, text="TOTAL:", font=('TkDefaultFont', 12, 'bold')).pack(side='left', padx=10,
                                                                                             pady=5)
        ttk.Label(total_label_frame, textvariable=self.total_var, font=('TkDefaultFont', 12, 'bold')).pack(side='left',
                                                                                                           padx=10,
                                                                                                           pady=5)

        # Botões Salvar/Cancelar
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side='right')

        self.save_button = ttk.Button(button_frame, text="Salvar", command=self._on_save)
        self.save_button.pack(side='left', padx=5, pady=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self._on_close_window)
        self.cancel_button.pack(side='left', padx=5, pady=5)

    def _load_data(self):
        """Carrega dados se estiver no modo 'edit' ou 'view'."""
        if self.mode in ('edit', 'view') and self.pedido_data:
            pedido_info = self.pedido_data.get('pedido_info', {})
            itens_info = self.pedido_data.get('itens', [])

            # Carrega Cliente
            cliente_id = pedido_info.get('cliente_id')
            cliente_nome = self.cliente_id_to_nome.get(cliente_id)
            if cliente_nome:
                self.cliente_var.set(cliente_nome)

            # Carrega Data
            self.data_var.set(pedido_info.get('data', ''))

            # Carrega Itens
            for item in itens_info:
                self._adicionar_item_na_tabela(
                    produto=item['produto'],
                    qtd=item['quantidade'],
                    preco_unit=item['preco_unit']
                )

            self._recalcular_total()  # Atualiza o total

        # Define o estado inicial do 'dirty' flag (só depois de carregar tudo)
        self.after(100, lambda: self.is_dirty.set(False))

    def _configure_states(self):
        """Desabilita campos se estiver no modo 'view'."""
        if self.is_readonly:
            self.cliente_combo.config(state='disabled')
            self.data_entry.config(state='disabled')
            self.itens_add_frame.config(text="Itens do Pedido")  # Muda o título

            # Esconde/desabilita widgets de adicionar item
            self.item_produto_entry.grid_remove()
            self.item_qtd_entry.grid_remove()
            self.item_preco_entry.grid_remove()
            self.add_item_button.grid_remove()
            self.remove_item_button.grid_remove()
            # Esconde labels
            for w in self.itens_add_frame.grid_slaves():
                if w not in (self.add_item_button, self.remove_item_button):
                    w.grid_remove()

            self.save_button.config(state='disabled')
            self.cancel_button.config(text="Fechar")  # Muda texto do botão

    def _mark_as_dirty(self, *args):
        """Marca o formulário como 'sujo' (dados alterados)."""
        self.is_dirty.set(True)

    def _on_item_select(self, event=None):
        """Habilita/desabilita botão 'Remover'."""
        if self.is_readonly:
            return
        if self.itens_tree.selection():
            self.remove_item_button.config(state='normal')
        else:
            self.remove_item_button.config(state='disabled')

    # --- Funções de Validação Locais ---
    # (Usadas aqui pois são específicas do formulário de itens)

    def _validate_not_empty(self, value, field_name):
        """Validação local simples."""
        if not value or not value.strip():
            messagebox.showwarning("Campo Obrigatório", f"O campo '{field_name}' não pode estar vazio.", parent=self)
            return False
        return True

    def _validate_positive_integer(self, value_str, field_name):
        """Validação local para inteiros positivos."""
        try:
            value = int(value_str)
            if value > 0:
                return True, value
            else:
                messagebox.showwarning("Valor Inválido", f"O campo '{field_name}' deve ser um número inteiro positivo.",
                                       parent=self)
                return False, 0
        except ValueError:
            messagebox.showwarning("Formato Inválido", f"O campo '{field_name}' deve ser um número inteiro.",
                                   parent=self)
            return False, 0

    def _validate_positive_float(self, value_str, field_name):
        """Validação local para floats positivos."""
        value_str = value_str.replace(',', '.')  # Aceita vírgula
        try:
            value = float(value_str)
            if value > 0:
                return True, value
            else:
                messagebox.showwarning("Valor Inválido", f"O campo '{field_name}' deve ser um número positivo.",
                                       parent=self)
                return False, 0.0
        except ValueError:
            messagebox.showwarning("Formato Inválido", f"O campo '{field_name}' deve ser um número (ex: 10.50).",
                                   parent=self)
            return False, 0.0

    def _validate_date_format(self, date_str):
        """Validação local para data (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            messagebox.showwarning("Formato Inválido", "A Data deve estar no formato AAAA-MM-DD.", parent=self)
            return False

    # --- Lógica de Itens ---

    def _adicionar_item(self):
        """Valida e adiciona um item na tabela."""
        produto = self.item_produto_var.get().strip()
        qtd_str = self.item_qtd_var.get().strip()
        preco_str = self.item_preco_var.get().strip()

        # Validação
        if not self._validate_not_empty(produto, "Produto"):
            self.item_produto_entry.focus()
            return

        valid_qtd, qtd_val = self._validate_positive_integer(qtd_str, "Quantidade")
        if not valid_qtd:
            self.item_qtd_entry.focus()
            return

        valid_preco, preco_val = self._validate_positive_float(preco_str, "Preço Unit.")
        if not valid_preco:
            self.item_preco_entry.focus()
            return

        # Adiciona na tabela
        self._adicionar_item_na_tabela(produto, qtd_val, preco_val)

        # Limpa os campos de entrada
        self.item_produto_var.set("")
        self.item_qtd_var.set("")
        self.item_preco_var.set("")

        self._recalcular_total()
        self.itens_changed.set(True)  # Marca que a lista de itens mudou
        self.item_produto_entry.focus()

    def _adicionar_item_na_tabela(self, produto, qtd, preco_unit):
        """Insere o item no Treeview e no dicionário de dados."""
        subtotal = qtd * preco_unit

        # Formata para exibição
        preco_f = f"{preco_unit:.2f}"
        subtotal_f = f"{subtotal:.2f}"

        # Adiciona no Treeview
        item_id = f"item_{self.item_counter}"
        self.item_counter += 1

        self.itens_tree.insert('', 'end', iid=item_id, values=(produto, qtd, preco_f, subtotal_f))

        # Guarda os dados *não* formatados (para salvar no DB)
        self.itens_tree_data[item_id] = {
            'produto': produto,
            'quantidade': qtd,
            'preco_unit': preco_unit
        }

    def _remover_item(self):
        """Remove o item selecionado da tabela."""
        try:
            selected_item_id = self.itens_tree.selection()[0]

            # Remove do dicionário de dados
            if selected_item_id in self.itens_tree_data:
                del self.itens_tree_data[selected_item_id]

            # Remove do Treeview
            self.itens_tree.delete(selected_item_id)

            self._recalcular_total()
            self.itens_changed.set(True)  # Marca que a lista de itens mudou

        except IndexError:
            # Isso não deve acontecer se o botão estiver habilitado/desabilitado corretamente
            log.warning("Tentativa de remover item sem seleção.")

    def _recalcular_total(self):
        """Calcula o total com base nos itens no dicionário de dados."""
        total = 0.0
        for item_id in self.itens_tree_data:
            item = self.itens_tree_data[item_id]
            total += item['quantidade'] * item['preco_unit']

        self.total_var.set(f"R$ {total:.2f}")
        return total

    # --- Lógica de Salvar e Fechar ---

    def _on_save(self):
        """Valida os dados principais e chama o callback do controlador."""
        if self.is_readonly:
            return

        # 1. Validar Cliente
        cliente_nome = self.cliente_var.get()
        if not self._validate_not_empty(cliente_nome, "Cliente"):
            self.cliente_combo.focus()
            return

        cliente_id = self.cliente_nome_to_id.get(cliente_nome)
        if not cliente_id:
            messagebox.showwarning("Cliente Inválido", "Cliente selecionado não é válido.", parent=self)
            self.cliente_combo.focus()
            return

        # 2. Validar Data
        data_str = self.data_var.get().strip()
        if not self._validate_date_format(data_str):
            self.data_entry.focus()
            return

        # 3. Validar Itens
        if not self.itens_tree_data:
            messagebox.showwarning("Pedido Vazio", "O pedido deve conter pelo menos um item.", parent=self)
            return

        # 4. Montar dados para o callback
        total_calculado = self._recalcular_total()

        data_to_save = {
            'id': self.pedido_data.get('pedido_info', {}).get('id') if self.mode == 'edit' else None,
            'cliente_id': cliente_id,
            'data': data_str,
            'total': total_calculado,
            'itens': list(self.itens_tree_data.values())  # Envia a lista de dicionários
        }

        # 5. Chamar o callback
        if self.on_save_callback:
            success = self.on_save_callback(data_to_save)
            if success:
                self.is_dirty.set(False)  # Marca como "limpo"
                self.destroy()

    def _on_close_window(self):
        """Chamado ao clicar em 'Cancelar' ou no 'X'."""
        if self.is_readonly:
            self.destroy()
            return

        if self.is_dirty.get():
            if messagebox.askyesno("Descartar Alterações?",
                                   "Você possui alterações não salvas. Deseja realmente fechar?",
                                   parent=self):
                self.destroy()
        else:
            self.destroy()


# --- Bloco de Teste ---

if __name__ == "__main__":
    # Configuração de logging para teste
    logging.basicConfig(level=logging.DEBUG)

    root = tk.Tk()
    root.title("Teste de PedidoView")
    root.geometry("800x600")

    # --- Abas para teste ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    tab_list = ttk.Frame(notebook)
    tab_form = ttk.Frame(notebook)
    notebook.add(tab_list, text="Teste Lista")
    notebook.add(tab_form, text="Teste Formulário")


    # --- Teste da Lista (PedidoListView) ---

    def sim_search_pedido(term):
        print(f"TESTE: Buscando Pedido por '{term}'")
        view_list.refresh_treeview([(99, 'Cliente Buscado', '2025-10-25', 50.0)])


    def sim_refresh_pedido():
        print("TESTE: Atualizando lista de Pedidos")
        view_list.refresh_treeview(dados_pedidos_simulados)


    def sim_add_pedido():
        print("TESTE: Abrindo formulário de Novo Pedido")
        # Simula a busca de clientes
        clientes_simulados = [(1, 'Alice Silva'), (2, 'Bruno Costa')]
        form = PedidoFormWindow(root, mode='new', on_save=sim_save_new_pedido, all_clients_list=clientes_simulados)
        form.grab_set()


    def sim_edit_pedido(pedido_id):
        print(f"TESTE: Abrindo formulário de Editar Pedido ID {pedido_id}")
        clientes_simulados = [(1, 'Alice Silva'), (2, 'Bruno Costa')]
        # Simula busca de dados do pedido
        dados_form_simulados = {
            'pedido_info': {'id': pedido_id, 'cliente_id': 2, 'data': '2025-10-20', 'total': 120.50},
            'itens': [
                {'produto': 'Produto Teste 1', 'quantidade': 2, 'preco_unit': 60.25}
            ]
        }
        form = PedidoFormWindow(root, mode='edit', on_save=sim_save_edit_pedido, pedido_data=dados_form_simulados,
                                all_clients_list=clientes_simulados)
        form.grab_set()


    def sim_delete_pedido(pedido_id):
        print(f"TESTE: Excluindo Pedido ID {pedido_id}")
        if view_list.show_confirm("Teste de Exclusão", f"Excluir ID {pedido_id}?"):
            print("TESTE: Exclusão confirmada.")


    def sim_save_new_pedido(data):
        print(f"TESTE: Salvando NOVO Pedido: {data}")
        return True  # Simula sucesso


    def sim_save_edit_pedido(data):
        print(f"TESTE: Salvando Pedido EDITADO: {data}")
        return True  # Simula sucesso


    view_list = PedidoListView(tab_list)
    view_list.pack(fill="both", expand=True)
    view_list.set_callbacks(
        on_search=sim_search_pedido,
        on_refresh=sim_refresh_pedido,
        on_add=sim_add_pedido,
        on_edit=sim_edit_pedido,
        on_delete=sim_delete_pedido
    )

    dados_pedidos_simulados = [
        (1, 'Alice Silva', '2025-10-24', 199.90),
        (2, 'Bruno Costa', '2025-10-23', 85.00)
    ]
    view_list.refresh_treeview(dados_pedidos_simulados)

    # --- Teste do Formulário (PedidoFormWindow) ---
    print("TESTE: Abrindo formulário de teste (Modo 'edit')")
    clientes_simulados = [(1, 'Alice Silva'), (2, 'Bruno Costa')]
    dados_form_simulados = {
        'pedido_info': {'id': 1, 'cliente_id': 1, 'data': '2025-10-24', 'total': 199.90},
        'itens': [
            {'produto': 'Produto A', 'quantidade': 2, 'preco_unit': 50.00},
            {'produto': 'Produto B', 'quantidade': 1, 'preco_unit': 99.90}
        ]
    }
    form_teste = PedidoFormWindow(
        tab_form,
        mode='edit',
        on_save=sim_save_edit_pedido,
        pedido_data=dados_form_simulados,
        all_clients_list=clientes_simulados
    )
    # Não usamos grab_set() aqui para poder interagir com a janela principal

    root.mainloop()

