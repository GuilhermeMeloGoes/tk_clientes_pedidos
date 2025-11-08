import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List, Tuple


class ClientesViewFrame(ttk.Frame):
    """
    Frame principal para listar e gerenciar clientes.
    Contém a Treeview, botões de ação e barra de busca.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_open_new_callback: Callable[[], None],
                 on_open_edit_callback: Callable[[Dict[str, Any]], None],
                 on_delete_callback: Callable[[int], None],
                 on_search_callback: Callable[[str], None]
                 ):
        """
        Inicializa o frame da lista de clientes.

        :param master: O widget pai (ex: um Notebook ou a janela principal).
        :param on_open_new_callback: Callback para o botão 'Novo'.
        :param on_open_edit_callback: Callback para o botão 'Editar'.
        :param on_delete_callback: Callback para o botão 'Excluir'.
        :param on_search_callback: Callback para o botão 'Buscar'.
        """
        super().__init__(master, padding="10")

        self.on_open_new = on_open_new_callback
        self.on_open_edit = on_open_edit_callback
        self.on_delete = on_delete_callback
        self.on_search = on_search_callback

        # Variável de controle para a busca
        self.search_var = tk.StringVar()

        # Cria os widgets
        self.create_widgets()

    def create_widgets(self):
        """Cria e posiciona os widgets no frame."""

        # --- Frame de Ações (Topo) ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 10))

        # Busca
        ttk.Label(top_frame, text="Buscar:").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.search_button = ttk.Button(top_frame, text="Buscar", command=self._on_search_click)
        self.search_button.pack(side="left", padx=5)

        # Bind <Return> (Enter) na barra de busca
        self.search_entry.bind("<Return>", self._on_search_click)

        # Botões de Ação
        self.delete_button = ttk.Button(top_frame, text="Excluir", command=self._on_delete_click)
        self.delete_button.pack(side="right", padx=5)

        self.edit_button = ttk.Button(top_frame, text="Editar", command=self._on_edit_click)
        self.edit_button.pack(side="right", padx=5)

        self.new_button = ttk.Button(top_frame, text="Novo Cliente", command=self.on_open_new)
        self.new_button.pack(side="right", padx=5)

        # --- Frame da Treeview (Centro) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        # Colunas da Treeview
        columns = ("id", "nome", "email", "telefone")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configuração das Colunas
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50, stretch=False, anchor="center")

        self.tree.heading("nome", text="Nome")
        self.tree.column("nome", width=200)

        self.tree.heading("email", text="E-mail")
        self.tree.column("email", width=250)

        self.tree.heading("telefone", text="Telefone")
        self.tree.column("telefone", width=120, anchor="center")

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
            "nome": item_values[1],
            "email": item_values[2],
            "telefone": item_values[3]
        }
        return data

    def _on_search_click(self, event=None):
        """Callback do botão de busca (ou Enter)."""
        search_term = self.search_var.get().strip()
        self.on_search(search_term)

    def _on_edit_click(self):
        """Callback do botão 'Editar'."""
        selected_data = self._get_selected_item_data()
        if selected_data:
            self.on_open_edit(selected_data)
        else:
            messagebox.showinfo("Nenhum Cliente Selecionado",
                                "Por favor, selecione um cliente na lista para editar.",
                                parent=self)

    def _on_delete_click(self):
        """Callback do botão 'Excluir'."""
        selected_data = self._get_selected_item_data()

        if not selected_data:
            messagebox.showinfo("Nenhum Cliente Selecionado",
                                "Por favor, selecione um cliente na lista para excluir.",
                                parent=self)
            return

        # Confirmação de exclusão
        nome = selected_data['nome']
        if messagebox.askyesno("Confirmar Exclusão",
                               f"Tem certeza que deseja excluir o cliente '{nome}'?\n\n(ID: {selected_data['id']})",
                               parent=self):
            self.on_delete(selected_data['id'])

    def refresh_data(self, clientes_list: List[Tuple]):
        """
        Limpa a Treeview e a recarrega com novos dados.

        :param clientes_list: Uma lista de tuplas, onde cada tupla
                              corresponde aos dados de um cliente
                              (id, nome, email, telefone).
        """
        # Limpa todos os itens existentes
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere os novos dados
        for cliente_data in clientes_list:
            # (id, nome, email, telefone)
            self.tree.insert("", tk.END, values=cliente_data)

        # Limpa a barra de busca (opcional, mas bom para feedback)
        # self.search_var.set("")


# =============================================================================
# === CLASSE DO FORMULÁRIO (JÁ CRIADA ANTERIORMENTE) ===
# =============================================================================

class ClienteForm(tk.Toplevel):
    """
    Janela Toplevel modal para cadastrar ou editar um cliente.
    (Esta é a classe da sua solicitação anterior, mantida no mesmo arquivo)
    """

    def __init__(self,
                 master: tk.Tk,
                 on_save_callback: Callable[[Dict[str, Any]], None],
                 on_cancel_callback: Callable[[], None],
                 cliente: Optional[Dict[str, Any]] = None):
        """
        Inicializa o formulário.

        :param master: A janela principal (root).
        :param on_save_callback: Função a ser chamada ao salvar. Recebe um dict com os dados.
        :param on_cancel_callback: Função a ser chamada ao cancelar ou fechar.
        :param cliente: Um dicionário com dados do cliente para preencher (modo de edição).
        """
        super().__init__(master)

        # Configurações do Toplevel
        self.master = master
        self.on_save_callback = on_save_callback
        self.on_cancel_callback = on_cancel_callback
        self.current_cliente_id = cliente.get('id', None) if cliente else None

        if cliente:
            self.title("Editar Cliente")
        else:
            self.title("Novo Cliente")

        # Variáveis de controle do Tkinter
        self.nome_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.telefone_var = tk.StringVar()

        # Cria os widgets
        self.create_widgets()

        # Carrega os dados se for modo de edição
        if cliente:
            self.load_data(cliente)

        # Flag para verificar se o usuário alterou algum dado
        self.is_dirty = False
        # Adiciona traces *depois* de carregar os dados
        self.nome_var.trace_add("write", self._set_dirty)
        self.email_var.trace_add("write", self._set_dirty)
        self.telefone_var.trace_add("write", self._set_dirty)

        # Configuração de modal
        self.transient(master)  # Mantém a janela na frente
        self.grab_set()  # Torna a janela modal

        # Intercepta o botão de fechar (o "X")
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Centraliza a janela em relação ao 'master'
        self.center_window()

        # Foca no primeiro campo de entrada
        self.nome_entry.focus_set()

    def create_widgets(self):
        """Cria e posiciona os widgets no formulário."""

        # Frame principal com padding
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Campos do Formulário ---
        form_frame = ttk.Frame(main_frame)
        form_frame.grid(row=0, column=0, sticky="ew")

        # Nome
        ttk.Label(form_frame, text="Nome:*").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.nome_entry = ttk.Entry(form_frame, textvariable=self.nome_var, width=40)
        self.nome_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Email
        ttk.Label(form_frame, text="E-mail:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.email_entry = ttk.Entry(form_frame, textvariable=self.email_var, width=40)
        self.email_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # Telefone
        ttk.Label(form_frame, text="Telefone:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.telefone_entry = ttk.Entry(form_frame, textvariable=self.telefone_var, width=40)
        self.telefone_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))

        # Informa que * é obrigatório
        ttk.Label(form_frame, text="* campo obrigatório").grid(row=6, column=0, sticky="w", pady=(0, 10))

        # Configura a coluna do form_frame para expandir
        form_frame.columnconfigure(0, weight=1)

        # --- Botões ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky="e", pady=(10, 0))

        self.save_button = ttk.Button(button_frame, text="Salvar", command=self.on_save)
        self.save_button.grid(row=0, column=0, padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.on_cancel)
        self.cancel_button.grid(row=0, column=1, padx=5)

    def load_data(self, cliente: Dict[str, Any]):
        """Preenche os campos com os dados do cliente (modo de edit)."""
        self.nome_var.set(cliente.get('nome', ''))
        self.email_var.set(cliente.get('email', ''))
        self.telefone_var.set(cliente.get('telefone', ''))

    def _set_dirty(self, *args):
        """Marca o formulário como 'modificado'."""
        self.is_dirty = True

    def validate(self) -> bool:
        """
        Valida os campos do formulário antes de salvar.
        Retorna True se válido, False caso contrário.
        """
        nome = self.nome_var.get().strip()
        email = self.email_var.get().strip()
        telefone = self.telefone_var.get().strip()

        # 1. Validação do Nome (Obrigatório)
        if not nome:
            messagebox.showwarning("Campo Obrigatório", "O campo 'Nome' é obrigatório.", parent=self)
            self.nome_entry.focus_set()
            return False

        # 2. Validação do E-mail (Formato simples)
        if email and ("@" not in email or "." not in email):
            messagebox.showwarning("Formato Inválido", "O 'E-mail' parece estar em um formato inválido.", parent=self)
            self.email_entry.focus_set()
            return False

        # 3. Validação do Telefone (8-15 dígitos)
        if telefone:
            # Remove caracteres comuns (parênteses, traços, espaços)
            telefone_digitos = "".join(filter(str.isdigit, telefone))

            if not (8 <= len(telefone_digitos) <= 15):
                messagebox.showwarning("Formato Inválido",
                                       "O 'Telefone' deve ter entre 8 e 15 dígitos.",
                                       parent=self)
                self.telefone_entry.focus_set()
                return False

            # (Opcional) Salva apenas os dígitos de volta na variável
            # self.telefone_var.set(telefone_digitos)

        return True

    def on_save(self):
        """Callback do botão 'Salvar'."""
        if not self.validate():
            return  # Para a execução se a validação falhar

        # Coleta os dados validados
        data = {
            "id": self.current_cliente_id,  # Será None para novos clientes
            "nome": self.nome_var.get().strip(),
            "email": self.email_var.get().strip(),
            "telefone": self.telefone_var.get().strip()
        }

        # Limpa os campos opcionais se estiverem vazios
        if not data["email"]:
            data["email"] = None
        if not data["telefone"]:
            data["telefone"] = None

        # Chama o callback externo
        try:
            self.on_save_callback(data)
            self.is_dirty = False  # Marca como "limpo" antes de fechar
            self.destroy()  # Fecha a janela
        except Exception as e:
            # Exibe erros que podem vir da camada de modelo/banco (ex: email duplicado)
            # Log simples no console
            print(f"ERRO [ClienteForm.on_save]: {e}")
            # Mensagem amigável para o usuário
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar:\n{e}", parent=self)

    def on_cancel(self):
        """Callback do botão 'Cancelar' ou do 'X' da janela."""

        # Verifica se há dados não salvos
        if self.is_dirty:
            if not messagebox.askyesno("Descartar Alterações?",
                                       "Você fez alterações que não foram salvas. "
                                       "Deseja fechar e descartar?",
                                       parent=self):
                return  # Não fecha

        self.on_cancel_callback()
        self.destroy()

    def center_window(self):
        """Centraliza o Toplevel na janela principal."""
        self.update_idletasks()  # Garante que as dimensões da janela estão atualizadas

        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()

        my_width = self.winfo_width()
        my_height = self.winfo_height()

        x = master_x + (master_width // 2) - (my_width // 2)
        y = master_y + (master_height // 2) - (my_height // 2)

        self.geometry(f'+{x}+{y}')  # Define apenas a posição


# --- Bloco de Teste ---
if __name__ == "__main__":

    # --- Configuração da Janela Principal de Teste ---
    root = tk.Tk()
    root.title("Teste da ClientesViewFrame")
    root.geometry("800x500")

    # Centraliza
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (800 // 2)
    y = (screen_height // 2) - (500 // 2)
    root.geometry(f'800x500+{x}+{y}')

    # --- Dados Falsos (Mock Data) ---
    mock_data = [
        (1, "Ana Silva", "ana.silva@email.com", "11987654321"),
        (2, "Bruno Costa", "bruno.costa@email.com", "21912345678"),
        (3, "Carla Dias", "carla.dias@email.com", "31998877665"),
        (4, "Daniel Moreira", "daniel.m@email.com", "41976543210"),
    ]


    # --- Callbacks de Teste ---
    def on_save_teste(data):
        print(f"--- SALVANDO (Mock) ---")
        print(data)
        messagebox.showinfo("Salvo (Teste)", "Cliente salvo! (Veja o console)\n"
                                             "A lista será recarregada agora.")
        # Simula a recarga
        # Em um app real, o controller buscaria os dados ATUALIZADOS do banco
        if data.get("id") is None:  # Novo cliente
            new_id = max(d[0] for d in mock_data) + 1 if mock_data else 1
            mock_data.append((new_id, data['nome'], data['email'], data['telefone']))
        else:  # Edição
            index = next((i for i, d in enumerate(mock_data) if d[0] == data['id']), -1)
            if index != -1:
                mock_data[index] = (data['id'], data['nome'], data['email'], data['telefone'])

        main_view.refresh_data(mock_data)  # Recarrega o frame principal


    def on_cancel_teste():
        print("--- CANCELADO (Formulário) ---")


    # Callbacks do Frame Principal
    def test_abrir_novo():
        print("--- TESTE: Abrir NOVO formulário ---")
        ClienteForm(root, on_save_teste, on_cancel_teste, cliente=None)


    def test_abrir_editar(data: Dict[str, Any]):
        print(f"--- TESTE: Abrir EDITAR formulário para: {data} ---")
        ClienteForm(root, on_save_teste, on_cancel_teste, cliente=data)


    def test_excluir(client_id: int):
        print(f"--- TESTE: Excluir cliente ID: {client_id} ---")

        # Simula a remoção do mock data
        global mock_data
        mock_data = [d for d in mock_data if d[0] != client_id]
        main_view.refresh_data(mock_data)

        messagebox.showinfo("Excluído (Teste)", f"Cliente ID {client_id} excluído.")


    def test_buscar(termo: str):
        print(f"--- TESTE: Buscando por: '{termo}' ---")
        if not termo:
            main_v.refresh_data(mock_data)  # Mostra tudo se a busca estiver vazia
            return

        termo = termo.lower()
        resultados = [
            d for d in mock_data
            if termo in d[1].lower() or (d[2] and termo in d[2].lower())
        ]
        main_view.refresh_data(resultados)


    # --- Instanciando o Frame Principal ---
    main_view = ClientesViewFrame(
        root,
        on_open_new_callback=test_abrir_novo,
        on_open_edit_callback=test_abrir_editar,
        on_delete_callback=test_excluir,
        on_search_callback=test_buscar
    )
    main_view.pack(fill="both", expand=True)

    # Carrega os dados iniciais
    main_view.refresh_data(mock_data)

    root.mainloop()