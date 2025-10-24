import tkinter as tk
from tkinter import ttk, messagebox
import logging
import re  # Importa 're' para a validação de email

log = logging.getLogger(__name__)


class ClienteListView(ttk.Frame):
    """
    View principal para listar, buscar e gerenciar Clientes.
    Usa callbacks para se comunicar com o controlador (main.py).
    """

    def __init__(self, parent):
        super().__init__(parent)

        # Callbacks (serão definidos pelo controlador via set_callbacks)
        self.on_search = None
        self.on_add = None
        self.on_edit = None
        self.on_delete = None

        self._setup_widgets()

    def set_callbacks(self, on_search, on_add, on_edit, on_delete):
        """Define as funções de callback do controlador."""
        self.on_search = on_search
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

        add_button = ttk.Button(top_frame, text="Novo Cliente", command=self._on_add_click)
        add_button.pack(side='right', padx=5)

        self.edit_button = ttk.Button(top_frame, text="Editar Cliente", state='disabled', command=self._on_edit_click)
        self.edit_button.pack(side='right', padx=5)

        self.delete_button = ttk.Button(top_frame, text="Excluir Cliente", state='disabled',
                                        command=self._on_delete_click)
        self.delete_button.pack(side='right')

        # Bind <Return> (Enter) na barra de busca para acionar a busca
        search_entry.bind('<Return>', self._on_search_click)

        # --- Treeview para listar clientes ---
        columns = ('id', 'nome', 'email', 'telefone')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')

        # Define cabeçalhos
        self.tree.heading('id', text='ID')
        self.tree.heading('nome', text='Nome')
        self.tree.heading('email', text='E-mail')
        self.tree.heading('telefone', text='Telefone')

        # Define largura das colunas
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('nome', width=250)
        self.tree.column('email', width=250)
        self.tree.column('telefone', width=150)

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
        """Retorna o ID do cliente selecionado no Treeview."""
        try:
            selected_item = self.tree.selection()[0]
            # O ID está na coluna 'id' (primeiro valor da tupla 'values')
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

    def _on_add_click(self):
        """Callback para o botão 'Novo Cliente'."""
        if self.on_add:
            self.on_add()

    def _on_edit_click(self):
        """Callback para o botão 'Editar Cliente'."""
        selected_id = self._get_selected_id()
        if selected_id and self.on_edit:
            self.on_edit(selected_id)

    def _on_double_click(self, event):
        """Callback para clique duplo (aciona edição)."""
        # Verifica se o clique foi em um item, não no cabeçalho
        if self.tree.identify_region(event.x, event.y) == "cell":
            self._on_edit_click()

    def _on_delete_click(self):
        """Callback para o botão 'Excluir Cliente'."""
        selected_id = self._get_selected_id()
        if selected_id and self.on_delete:
            self.on_delete(selected_id)

    def refresh_treeview(self, data):
        """Limpa e recarrega o Treeview com novos dados."""
        # Limpa a tabela
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Insere novos dados
        # Espera dados no formato [(id, nome, email, telefone), ...]
        for row in data:
            self.tree.insert('', 'end', values=row)

        # Limpa a seleção após recarregar
        self._on_item_select()

    def show_confirm(self, title, message):
        """Exibe um popup de confirmação (usado pelo controlador)."""
        return messagebox.askyesno(title, message, parent=self)


# --- Formulário de Cliente (Janela Toplevel) ---

class ClienteFormWindow(tk.Toplevel):
    """
    Janela Toplevel para cadastrar ou editar um cliente.
    """

    def __init__(self, parent, mode='new', on_save=None, cliente_data=None):
        super().__init__(parent)
        self.transient(parent)  # Mantém a janela no topo
        self.resizable(False, False)

        self.mode = mode
        self.on_save_callback = on_save
        self.cliente_data = cliente_data if cliente_data else {}
        self.is_dirty = tk.BooleanVar(value=False)  # Flag para dados não salvos

        self.title("Novo Cliente" if self.mode == 'new' else "Editar Cliente")

        # --- Variáveis dos campos ---
        self.nome_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.telefone_var = tk.StringVar()

        self._setup_widgets()
        self._load_data()

        # Bind para o "X" da janela
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # Bind para rastrear alterações
        self.nome_var.trace_add("write", self._mark_as_dirty)
        self.email_var.trace_add("write", self._mark_as_dirty)
        self.telefone_var.trace_add("write", self._mark_as_dirty)

    def _setup_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)

        # --- Labels e Entradas ---
        ttk.Label(main_frame, text="Nome:").grid(row=0, column=0, sticky='w', pady=5)
        self.nome_entry = ttk.Entry(main_frame, textvariable=self.nome_var, width=40)
        self.nome_entry.grid(row=0, column=1, sticky='we', pady=5, padx=5)
        self.nome_entry.focus_set()  # Foco inicial

        ttk.Label(main_frame, text="E-mail:").grid(row=1, column=0, sticky='w', pady=5)
        self.email_entry = ttk.Entry(main_frame, textvariable=self.email_var, width=40)
        self.email_entry.grid(row=1, column=1, sticky='we', pady=5, padx=5)

        ttk.Label(main_frame, text="Telefone:").grid(row=2, column=0, sticky='w', pady=5)
        self.telefone_entry = ttk.Entry(main_frame, textvariable=self.telefone_var, width=40)
        self.telefone_entry.grid(row=2, column=1, sticky='we', pady=5, padx=5)

        # --- Botões ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(15, 0), sticky='e')

        self.save_button = ttk.Button(button_frame, text="Salvar", command=self._on_save_internal)
        self.save_button.pack(side='left', padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self._on_close_window)
        self.cancel_button.pack(side='left')

    def _load_data(self):
        """Carrega dados do cliente se estiver no modo 'edit'."""
        if self.mode == 'edit' and self.cliente_data:
            self.nome_var.set(self.cliente_data.get('nome', ''))
            self.email_var.set(self.cliente_data.get('email', ''))
            self.telefone_var.set(self.cliente_data.get('telefone', ''))

        # Reseta o 'dirty' flag após carregar os dados
        self.after(100, lambda: self.is_dirty.set(False))  # Atraso para o trace não disparar

    def _mark_as_dirty(self, *args):
        """Marca o formulário como 'sujo' (dados alterados)."""
        self.is_dirty.set(True)

    # --- Funções de Validação Locais ---
    # (Movidas para cá para remover a dependência do utils.py)

    def _validate_not_empty(self, value, field_name):
        """Validação local: campo não pode ser vazio."""
        if not value or not value.strip():
            messagebox.showwarning("Campo Obrigatório", f"O campo '{field_name}' não pode estar vazio.", parent=self)
            return False
        return True

    def _validate_email_format(self, email):
        """Validação local: formato de email simples (deve conter '@')."""
        # Um regex simples para email (pode ser melhorado se necessário)
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showwarning("Formato Inválido", "O formato do E-mail é inválido.", parent=self)
            return False
        return True

    def _validate_telefone_format(self, telefone):
        """Validação local: telefone deve ter 8-15 dígitos."""
        # Remove caracteres não numéricos (parênteses, traços)
        digits_only = re.sub(r'\D', '', telefone)

        if 8 <= len(digits_only) <= 15:
            return True
        else:
            messagebox.showwarning("Formato Inválido", "O Telefone deve conter entre 8 e 15 dígitos numéricos.",
                                   parent=self)
            return False

    def _validate_fields(self, data):
        """Valida os campos usando as funções locais."""
        nome = data['nome']
        email = data['email']
        telefone = data['telefone']

        # 1. Validação de Nome (Obrigatório)
        if not self._validate_not_empty(nome, "Nome"):
            self.nome_entry.focus()
            return False

        # 2. Validação de Email (Formato)
        if email:  # Email é opcional, mas se preenchido, deve ser válido
            if not self._validate_email_format(email):
                self.email_entry.focus()
                return False

        # 3. Validação de Telefone (Formato)
        if telefone:  # Telefone também é opcional
            if not self._validate_telefone_format(telefone):
                self.telefone_entry.focus()
                return False

        return True

    def _on_save_internal(self):
        """Lógica interna ao clicar em 'Salvar'."""
        data = {
            'id': self.cliente_data.get('id') if self.mode == 'edit' else None,
            'nome': self.nome_var.get().strip(),
            'email': self.email_var.get().strip(),
            'telefone': self.telefone_var.get().strip()
        }

        # Chama a validação local corrigida
        if not self._validate_fields(data):
            return  # A validação falhou

        if self.on_save_callback:
            # Chama o callback (no main.py) e verifica se foi bem sucedido
            success = self.on_save_callback(data)
            if success:
                self.is_dirty.set(False)  # Marca como "limpo" para fechar
                self.destroy()

    def _on_close_window(self):
        """Chamado ao clicar em 'Cancelar' ou no 'X'."""
        if self.is_dirty.get():
            if messagebox.askyesno("Descartar Alterações?",
                                   "Você possui alterações não salvas. Deseja realmente fechar?",
                                   parent=self):
                self.destroy()
        else:
            self.destroy()


# --- Bloco de Teste (para executar o arquivo isoladamente) ---

if __name__ == "__main__":
    # Configuração de logging para teste
    logging.basicConfig(level=logging.DEBUG)

    root = tk.Tk()
    root.title("Teste de ClienteListView")
    root.geometry("700x400")


    # --- Funções de Callback Simuladas ---
    def sim_search(term):
        print(f"TESTE: Buscando por '{term}'")
        # Simula dados de busca
        dados_simulados_busca = [
            (3, 'Cliente Encontrado', 'search@test.com', '99999999')
        ]
        view.refresh_treeview(dados_simulados_busca)


    def sim_add():
        print("TESTE: Abrindo formulário de Adicionar")
        form = ClienteFormWindow(root, mode='new', on_save=sim_save_new)
        form.grab_set()


    def sim_edit(client_id):
        print(f"TESTE: Abrindo formulário de Editar para ID {client_id}")
        # Simula a busca dos dados do cliente
        dados_cliente = {'id': client_id, 'nome': 'Cliente para Editar', 'email': 'edit@test.com',
                         'telefone': '12345678'}
        form = ClienteFormWindow(root, mode='edit', on_save=sim_save_edit, cliente_data=dados_cliente)
        form.grab_set()


    def sim_delete(client_id):
        print(f"TESTE: Excluindo cliente ID {client_id}")
        if view.show_confirm("Teste de Exclusão", f"Excluir ID {client_id}?"):
            print("TESTE: Exclusão confirmada.")
            # Simula a atualização da lista
            view.refresh_treeview(dados_simulados)  # Recarrega lista original
        else:
            print("TESTE: Exclusão cancelada.")


    # --- Funções de Save Simuladas ---
    def sim_save_new(data):
        print(f"TESTE: Salvando NOVO cliente: {data}")
        # Simula sucesso
        return True


    def sim_save_edit(data):
        print(f"TESTE: Salvando cliente EDITADO: {data}")
        # Simula falha
        # messagebox.showerror("Erro Simulado", "Não foi possível salvar.")
        # return False

        # Simula sucesso
        return True


    # --- Inicialização da View ---
    view = ClienteListView(root)
    view.pack(fill="both", expand=True)

    # Conecta os callbacks simulados
    view.set_callbacks(
        on_search=sim_search,
        on_add=sim_add,
        on_edit=sim_edit,
        on_delete=sim_delete
    )

    # Dados de teste
    dados_simulados = [
        (1, 'Alice Silva', 'alice@exemplo.com', '11987654321'),
        (2, 'Bruno Costa', 'bruno@exemplo.com', '21912345678')
    ]

    # Carrega os dados na view
    view.refresh_treeview(dados_simulados)

    root.mainloop()

