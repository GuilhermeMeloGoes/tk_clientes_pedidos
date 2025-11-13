"""
Views/Clientes_View.py

Define o frame (tela) da aba Clientes e o Toplevel (popup)
para cadastrar/editar um cliente.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List, Tuple
import re  # Para validar o email
import utils  # Importa o utils


# =============================================================================
# === FRAME DA LISTA DE CLIENTES ===
# =============================================================================

class ClientesViewFrame(ttk.Frame):
    """
    Frame principal para a aba Clientes.
    Contém a Treeview, busca e botões de ação.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_new_callback: Callable[[Optional[Dict[str, Any]]], None],
                 on_edit_callback: Callable[[Optional[Dict[str, Any]]], None],
                 on_delete_callback: Callable[[int], None],
                 on_search_callback: Callable[[str], None]
                 ):
        """
        Inicializa o frame de Clientes.

        :param master: O widget pai (a aba do Notebook).
        :param on_new_callback: Callback para o botão 'Novo'.
        :param on_edit_callback: Callback para o botão 'Editar'.
        :param on_delete_callback: Callback para o botão 'Excluir'.
        :param on_search_callback: Callback para o botão 'Buscar'.
        """
        super().__init__(master, padding="0")  # Padding 0, o frame pai (container) já tem

        # Callbacks
        self.on_new = on_new_callback
        self.on_edit = on_edit_callback
        self.on_delete = on_delete_callback
        self.on_search = on_search_callback

        # Variáveis de controle
        self.search_var = tk.StringVar()

        # Cria os widgets
        self.create_widgets()

    def create_widgets(self):
        """Cria e posiciona os widgets no frame."""

        # --- Frame de Ações e Busca (Topo) ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 10))

        # Busca
        ttk.Label(top_frame, text="Buscar (Nome/Email):").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        # Binda o <Return> (Enter) para a busca
        self.search_entry.bind("<Return>", self._on_search_click)

        self.search_button = ttk.Button(top_frame, text="Buscar", command=self._on_search_click)
        self.search_button.pack(side="left", padx=5)

        # Botões de Ação (alinhados à direita)
        self.delete_button = ttk.Button(top_frame, text="Excluir Selecionado", command=self._on_delete_click)
        self.delete_button.pack(side="right", padx=5)

        self.edit_button = ttk.Button(top_frame, text="Editar Selecionado", command=self._on_edit_click)
        self.edit_button.pack(side="right", padx=5)

        self.new_button = ttk.Button(top_frame, text="Novo Cliente", command=self._on_new_click)
        self.new_button.pack(side="right", padx=5)

        # --- Frame da Treeview (Centro) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        # Colunas da Treeview
        # O 'id' é a primeira coluna, mas não a exibimos (show="headings")
        columns = ("id", "nome", "email", "telefone")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configuração das Colunas
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=60, stretch=False, anchor="center")  # stretch=False para não expandir

        self.tree.heading("nome", text="Nome")
        self.tree.column("nome", width=300)  # Coluna larga

        self.tree.heading("email", text="E-mail")
        self.tree.column("email", width=300)

        self.tree.heading("telefone", text="Telefone")
        self.tree.column("telefone", width=150, anchor="center")

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

    def _get_selected_cliente_data(self) -> Optional[Dict[str, Any]]:
        """Helper para pegar os dados do item selecionado na Treeview."""
        try:
            selected_item = self.tree.selection()[0]  # Pega o primeiro (e único) item selecionado
            values = self.tree.item(selected_item, "values")

            # Recria o dicionário de dados (precisa bater com o formulário)
            cliente_data = {
                "id": int(values[0]),
                "nome": values[1],
                "email": values[2],
                "telefone": values[3]
            }
            return cliente_data

        except IndexError:
            messagebox.showwarning("Nenhum Cliente Selecionado",
                                   "Por favor, selecione um cliente na lista primeiro.",
                                   parent=self)
            return None
        except (ValueError, TypeError):
            messagebox.showerror("Erro de Seleção",
                                 "Não foi possível identificar o cliente selecionado.",
                                 parent=self)
            return None

    def _on_search_click(self, event=None):
        """Callback do botão de busca (ou Enter)."""
        search_term = self.search_var.get().strip()
        # Chama o callback do main.py
        self.on_search(search_term)

    def _on_new_click(self):
        """Callback do botão 'Novo'."""
        # Chama o callback do main.py (sem dados)
        self.on_new(None)

    def _on_edit_click(self):
        """Callback do botão 'Editar'."""
        cliente_data = self._get_selected_cliente_data()
        if cliente_data is None:
            return

        # Chama o callback do main.py (com dados)
        self.on_edit(cliente_data)

    def _on_delete_click(self):
        """Callback do botão 'Excluir'."""
        cliente_data = self._get_selected_cliente_data()
        if cliente_data is None:
            return

        cliente_id = cliente_data['id']
        cliente_nome = cliente_data['nome']

        if messagebox.askyesno("Confirmar Exclusão",
                               f"Tem certeza que deseja excluir o cliente:\n\n{cliente_nome} (ID: {cliente_id})?",
                               parent=self, icon="warning"):
            # Chama o callback do main.py
            self.on_delete(cliente_id)

    def refresh_data(self, clientes_list: List[Tuple]):
        """
        Limpa a Treeview e a recarrega com novos dados.

        :param clientes_list: Uma lista de tuplas, onde cada tupla
                               é (id, nome, email, telefone).
        """
        # Limpa todos os itens existentes
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere os novos dados
        for cliente_data_tuple in clientes_list:

            # CORREÇÃO: Converte 'None' em string vazia ''
            # para evitar o bug do "None" na UI.
            values = list(cliente_data_tuple)
            for i in range(1, len(values)):  # Começa do 1 (ignora o ID)
                if values[i] is None:
                    values[i] = ""

            self.tree.insert("", tk.END, values=tuple(values))


# =============================================================================
# === FORMULÁRIO DE CLIENTE (POPUP TOPLEVEL) ===
# =============================================================================

class ClienteForm(tk.Toplevel):
    """
    Janela Toplevel (popup) para cadastrar ou editar um Cliente.
    """

    def __init__(self,
                 master: tk.Widget,
                 on_save_callback: Callable[[Dict[str, Any]], None],
                 on_cancel_callback: Callable[[], None],
                 on_dirty_callback: Callable[[tk.Toplevel], None],  # <-- CORRIGIDO
                 cliente_data: Optional[Dict[str, Any]] = None
                 ):
        """
        Inicializa o formulário.

        :param master: O widget pai (a janela principal 'App').
        :param on_save_callback: Função a ser chamada ao salvar.
        :param on_cancel_callback: Função a ser chamada ao fechar/cancelar.
        :param on_dirty_callback: Função a ser chamada quando dados mudam.
        :param cliente_data: (Opcional) Dados para preencher (modo 'Editar').
        """
        super().__init__(master)

        self.on_save = on_save_callback
        self.on_cancel = on_cancel_callback
        self.on_dirty = on_dirty_callback  # <-- CORRIGIDO

        self.is_edit_mode = cliente_data is not None
        # CORREÇÃO: Verifica se cliente_data não é None antes de .get()
        self.cliente_id = cliente_data.get('id') if self.is_edit_mode and cliente_data else None

        # --- Configuração da Janela ---
        self.title("Editar Cliente" if self.is_edit_mode else "Novo Cliente")
        self.transient(master)  # Mantém sobre a janela principal
        self.grab_set()  # Modal
        self.resizable(False, False)

        # --- Estado Interno ---
        self.is_dirty = False  # Rastreia alterações não salvas

        # --- Variáveis de Controle (StringVars) ---
        # CORREÇÃO: Verifica se cliente_data é None (Modo Novo)
        if self.is_edit_mode and cliente_data:
            nome_val = cliente_data.get('nome', '')
            email_val = cliente_data.get('email', '')
            telefone_val = cliente_data.get('telefone', '')
        else:
            # Modo "Novo", todos os campos começam vazios
            nome_val, email_val, telefone_val = '', '', ''

        self.nome_var = tk.StringVar(value=nome_val)
        self.email_var = tk.StringVar(value=email_val)
        self.telefone_var = tk.StringVar(value=telefone_val)

        # Registra o callback para quando o usuário digitar
        self.nome_var.trace_add("write", self._set_dirty)
        self.email_var.trace_add("write", self._set_dirty)
        self.telefone_var.trace_add("write", self._set_dirty)

        # --- Cria os Widgets ---
        self.create_widgets()

        # Centraliza a janela
        utils.center_window(self)

        # Foca no primeiro campo
        self.nome_entry.focus_set()

        # Intercepta o 'X' da janela
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

    def create_widgets(self):
        """Cria e posiciona os widgets no formulário."""

        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill="both", expand=True)

        # --- Frame dos Campos (Grid) ---
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill="x")

        # Configura o grid
        fields_frame.columnconfigure(1, weight=1)  # Coluna 1 (Entry) expande

        # Nome
        ttk.Label(fields_frame, text="Nome:*").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.nome_entry = ttk.Entry(fields_frame, textvariable=self.nome_var, width=50)
        self.nome_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # E-mail
        ttk.Label(fields_frame, text="E-mail:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.email_entry = ttk.Entry(fields_frame, textvariable=self.email_var, width=50)
        self.email_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Telefone
        ttk.Label(fields_frame, text="Telefone:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.telefone_entry = ttk.Entry(fields_frame, textvariable=self.telefone_var, width=50)
        self.telefone_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Label de ajuda
        ttk.Label(fields_frame, text="* campo obrigatório",
                  style="Secondary.TLabel").grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # --- Frame dos Botões ---
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(15, 0))  # Espaço acima

        # (Os botões são alinhados à direita por padrão no pack)
        self.cancel_button = ttk.Button(buttons_frame, text="Cancelar", command=self._on_close_window)
        self.cancel_button.pack(side="right", padx=5)

        self.save_button = ttk.Button(buttons_frame, text="Salvar", command=self._on_save_click)
        self.save_button.pack(side="right", padx=5)

        # Binda o <Return> (Enter) para salvar
        self.bind("<Return>", self._on_save_click)

    def _set_dirty(self, *args):
        """
        Marca o formulário como 'sujo' (dados não salvos)
        e notifica o 'main.py' (Controlador).
        """
        if not self.is_dirty:
            self.is_dirty = True
            # Notifica o main.py (Controlador)
            self.on_dirty(self)  # <-- CORRIGIDO
            print("INFO [ClienteForm]: Formulário marcado como 'dirty'.")

    def _validate_form(self) -> bool:
        """
        Valida os campos do formulário antes de salvar.
        Retorna True se válido, False caso contrário.
        """
        # Pega os valores (removendo espaços extras)
        nome = self.nome_var.get().strip()
        email = self.email_var.get().strip()
        telefone = self.telefone_var.get().strip()

        # 1. Validação do Nome (Obrigatório)
        if not nome:
            messagebox.showwarning("Campo Obrigatório", "O campo 'Nome' é obrigatório.", parent=self)
            self.nome_entry.focus_set()
            return False

        # 2. Validação do E-mail (Formato simples)
        # (Só valida se o campo não estiver vazio)
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showwarning("Formato Inválido", "O 'E-mail' parece estar em um formato inválido.", parent=self)
            self.email_entry.focus_set()
            return False

        # 3. Validação do Telefone (8-15 dígitos)
        # (Só valida se o campo não estiver vazio)
        if telefone:
            telefone_digitos = "".join(filter(str.isdigit, telefone))

            if not (8 <= len(telefone_digitos) <= 15):
                messagebox.showwarning("Formato Inválido",
                                       "O 'Telefone' deve ter entre 8 e 15 dígitos.",
                                       parent=self)
                self.telefone_entry.focus_set()
                return False

        return True

    def _on_save_click(self, event=None):
        """Callback do botão 'Salvar'."""

        # 1. Valida o formulário
        if not self._validate_form():
            return  # Validação falhou

        # 2. Prepara os dados para o 'main.py'
        cliente_data = {
            "id": self.cliente_id,  # (Será None se for 'Novo')
            "nome": self.nome_var.get().strip(),
            "email": self.email_var.get().strip() or None,  # Salva None se vazio
            "telefone": self.telefone_var.get().strip() or None  # Salva None se vazio
        }

        try:
            # 3. Chama o callback do 'main.py' (que chama o 'models')
            self.on_save(cliente_data)

            # 4. Se o 'on_save' (models) não deu erro, fecha
            self.is_dirty = False  # Marcar como "não sujo" antes de fechar
            self.destroy()  # Fecha o Toplevel
            self.on_cancel()  # Notifica o 'main'

        except Exception as e:
            # Se o 'main.save_cliente' (models) levantar o erro
            # (ex: email duplicado), o 'except' dele lá no 'main'
            # vai mostrar a messagebox.
            # O 'raise e' dele vai fazer este 'except' ser ativado,
            # impedindo que o form seja fechado.
            print(f"INFO [ClienteForm.on_save]: Ocorreu um erro ao salvar (esperado), formulário não será fechado.")

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
                return  # Não fecha

        # Se não estiver 'dirty' ou se o usuário confirmou
        self.is_dirty = False
        self.destroy()
        self.on_cancel()
