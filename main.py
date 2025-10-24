import tkinter as tk
from tkinter import ttk, messagebox
import logging
import logging.config
import sys

# Importa o inicializador do DB
import db

# Importa os Models
try:
    from models import ClienteModel, PedidoModel
except ImportError:
    logging.critical("Falha ao importar os módulos 'models'. O arquivo 'models.py' existe?")
    sys.exit(1)

# Importa as Views
try:
    from views.clientes_view import ClienteListView, ClienteFormWindow
    from views.pedidos_view import PedidoListView, PedidoFormWindow
except ImportError as e:
    logging.critical(f"Falha ao importar os módulos 'views'. Verifique os arquivos: {e}")
    sys.exit(1)


# Configuração centralizada de Logging
def setup_logging():
    """Configura o logging para a aplicação."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler()  # Saída para o console
            # Você pode adicionar logging.FileHandler('app.log') aqui se quiser
        ]
    )
    # Define o loglevel do DB (que é muito verboso) para WARNING
    logging.getLogger('db').setLevel(logging.WARNING)


log = logging.getLogger(__name__)


class MainApplication(tk.Tk):
    """Classe principal da aplicação."""

    def __init__(self):
        super().__init__()
        self.title("Sistema de Clientes e Pedidos")
        self.geometry("800x600")

        self.cliente_model = None
        self.pedido_model = None

        try:
            self._instantiate_models()
        except Exception as e:
            log.critical(f"Falha ao instanciar modelos: {e}", exc_info=True)
            messagebox.showerror("Erro Crítico", f"Não foi possível iniciar os modelos de dados:\n{e}")
            self.destroy()
            return

        self._setup_ui()

        # Inicia carregando os dados nas abas
        self._refresh_cliente_list()
        self._refresh_pedido_list()

    def _instantiate_models(self):
        """Instancia os modelos de dados."""
        self.cliente_model = ClienteModel()
        self.pedido_model = PedidoModel()
        log.info("Modelos de dados instanciados.")

    def _setup_ui(self):
        """Configura a interface principal com abas."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # Configura as abas
        self._setup_clientes_tab()
        self._setup_pedidos_tab()

    def _setup_clientes_tab(self):
        """Cria e configura a aba de Clientes."""
        self.cliente_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.cliente_frame, text='Clientes')

        self.cliente_view = ClienteListView(self.cliente_frame)
        self.cliente_view.pack(fill="both", expand=True)

        # --- Conecta os callbacks (Funções do Controlador) ---
        self.cliente_view.set_callbacks(
            on_search=self._refresh_cliente_list,
            on_add=self._handle_add_cliente,
            on_edit=self._handle_edit_cliente,
            on_delete=self._handle_delete_cliente
        )

    def _setup_pedidos_tab(self):
        """Cria e configura a aba de Pedidos."""
        self.pedido_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.pedido_frame, text='Pedidos')

        self.pedido_view = PedidoListView(self.pedido_frame)
        self.pedido_view.pack(fill="both", expand=True)

        # --- Conecta os callbacks (Funções do Controlador) ---
        self.pedido_view.set_callbacks(
            on_search=self._refresh_pedido_list,
            on_refresh=self._refresh_pedido_list,  # Botão de atualizar
            on_add=self._handle_add_pedido,
            on_edit=self._handle_edit_pedido,
            on_delete=self._handle_delete_pedido
        )

    # --- LÓGICA DE CONTROLADOR: CLIENTES ---

    def _refresh_cliente_list(self, search_term=""):
        """Busca clientes no modelo e atualiza a view."""
        log.info(f"MAIN: Buscando clientes com termo: '{search_term}'")
        try:
            clientes = self.cliente_model.find_clients(search_term)
            self.cliente_view.refresh_treeview(clientes)
        except Exception as e:
            log.error(f"Erro ao buscar clientes: {e}", exc_info=True)
            messagebox.showerror("Erro de Busca", f"Ocorreu um erro ao buscar clientes:\n{e}")

    def _handle_add_cliente(self):
        """Abre o formulário para um novo cliente."""
        log.info("MAIN: Abrindo formulário de novo cliente.")
        form = ClienteFormWindow(self, mode='new', on_save=self._save_new_cliente)
        form.grab_set()  # Torna a janela modal

    def _handle_edit_cliente(self, cliente_id):
        """Abre o formulário para editar um cliente existente."""
        log.info(f"MAIN: Abrindo formulário de edição para cliente ID: {cliente_id}")
        try:
            cliente_data = self.cliente_model.get_client_by_id(cliente_id)
            if not cliente_data:
                messagebox.showerror("Erro", "Cliente não encontrado. A lista pode estar desatualizada.")
                self._refresh_cliente_list()
                return

            form = ClienteFormWindow(
                self,
                mode='edit',
                on_save=self._save_edited_cliente,
                cliente_data=cliente_data
            )
            form.grab_set()
        except Exception as e:
            log.error(f"Erro ao buscar cliente para edição: {e}", exc_info=True)
            messagebox.showerror("Erro", f"Ocorreu um erro ao buscar dados do cliente:\n{e}")

    def _save_new_cliente(self, data):
        """Salva o novo cliente no modelo."""
        log.info("MAIN: Salvando novo cliente.")
        try:
            self.cliente_model.add_client(data['nome'], data['email'], data['telefone'])
            messagebox.showinfo("Sucesso", "Cliente cadastrado com sucesso!")
            self._refresh_cliente_list()  # Atualiza a lista
            return True  # Indica sucesso para fechar o formulário
        except Exception as e:
            log.error(f"Erro ao salvar novo cliente: {e}", exc_info=True)
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar o cliente:\n{e}")
            return False  # Indica falha

    def _save_edited_cliente(self, data):
        """Salva o cliente editado no modelo."""
        log.info(f"MAIN: Salvando edições do cliente ID: {data['id']}")
        try:
            self.cliente_model.update_client(data['id'], data['nome'], data['email'], data['telefone'])
            messagebox.showinfo("Sucesso", "Cliente atualizado com sucesso!")
            self._refresh_cliente_list()  # Atualiza a lista
            return True  # Indica sucesso
        except Exception as e:
            log.error(f"Erro ao editar cliente: {e}", exc_info=True)
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao atualizar o cliente:\n{e}")
            return False

    def _handle_delete_cliente(self, cliente_id):
        """Exclui um cliente (após confirmação)."""
        log.info(f"MAIN: Tentativa de exclusão do cliente ID: {cliente_id}")
        try:
            # Pede confirmação (o show_confirm está na view)
            if self.cliente_view.show_confirm("Confirmar Exclusão",
                                              "Tem certeza que deseja excluir este cliente?\nPedidos associados a ele NÃO serão excluídos."):

                result = self.cliente_model.delete_client(cliente_id)

                if result.get("success"):
                    messagebox.showinfo("Sucesso", "Cliente excluído com sucesso.")
                    self._refresh_cliente_list()
                    # Se excluiu o cliente, é bom atualizar a lista de pedidos também
                    self._refresh_pedido_list()
                else:
                    messagebox.showwarning("Aviso", result.get("message", "Não foi possível excluir o cliente."))

        except Exception as e:
            log.error(f"Erro ao excluir cliente: {e}", exc_info=True)
            messagebox.showerror("Erro ao Excluir", f"Ocorreu um erro ao excluir o cliente:\n{e}")

    # --- LÓGICA DE CONTROLADOR: PEDIDOS ---

    def _refresh_pedido_list(self, search_term=""):
        """Busca pedidos no modelo e atualiza a view."""
        log.info(f"MAIN: Buscando pedidos com termo: '{search_term}'")
        try:
            pedidos = self.pedido_model.find_pedidos(search_term)
            self.pedido_view.refresh_treeview(pedidos)
        except Exception as e:
            log.error(f"Erro ao buscar pedidos: {e}", exc_info=True)
            messagebox.showerror("Erro de Busca", f"Ocorreu um erro ao buscar pedidos:\n{e}")

    def _get_all_clients_list(self):
        """Busca lista simples de clientes (id, nome) para o Combobox."""
        try:
            return self.cliente_model.get_all_clients_list()
        except Exception as e:
            log.error(f"Erro ao buscar lista de clientes para formulário: {e}", exc_info=True)
            return []

    def _handle_add_pedido(self):
        """Abre o formulário para um novo pedido."""
        log.info("MAIN: Abrindo formulário de novo pedido.")

        all_clients = self._get_all_clients_list()
        if not all_clients:
            messagebox.showwarning("Aviso", "Não é possível criar um pedido, pois não há clientes cadastrados.")
            log.warning("MAIN: Tentativa de criar pedido sem clientes cadastrados.")
            return

        form = PedidoFormWindow(
            self,
            mode='new',
            all_clients_list=all_clients,
            on_save=self._save_new_pedido
        )
        form.grab_set()

    def _handle_edit_pedido(self, pedido_id):
        """Abre o formulário para editar um pedido existente."""
        log.info(f"MAIN: Abrindo formulário de edição para pedido ID: {pedido_id}")
        try:
            pedido_data = self.pedido_model.get_pedido_details(pedido_id)
            if not pedido_data:
                messagebox.showerror("Erro", "Pedido não encontrado. A lista pode estar desatualizada.")
                self._refresh_pedido_list()
                return

            all_clients = self._get_all_clients_list()

            form = PedidoFormWindow(
                self,
                mode='edit',
                pedido_data=pedido_data,
                all_clients_list=all_clients,
                on_save=self._save_edited_pedido
            )
            form.grab_set()
        except Exception as e:
            log.error(f"Erro ao buscar pedido para edição: {e}", exc_info=True)
            messagebox.showerror("Erro", f"Ocorreu um erro ao buscar dados do pedido:\n{e}")

    def _save_new_pedido(self, data):
        """Salva o novo pedido no modelo."""
        log.info("MAIN: Salvando novo pedido.")
        try:
            self.pedido_model.salvar_pedido_transacional(
                cliente_id=data['cliente_id'],
                data_pedido=data['data'],
                itens=data['itens'],
                total=data['total']
            )
            messagebox.showinfo("Sucesso", "Pedido cadastrado com sucesso!")
            self._refresh_pedido_list()
            return True
        except Exception as e:
            log.error(f"Erro ao salvar novo pedido: {e}", exc_info=True)
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar o pedido:\n{e}")
            return False

    def _save_edited_pedido(self, data):
        """Salva o pedido editado no modelo."""
        log.info(f"MAIN: Salvando edições do pedido ID: {data['id']}")
        try:
            self.pedido_model.editar_pedido_transacional(
                pedido_id=data['id'],
                cliente_id=data['cliente_id'],
                data_pedido=data['data'],
                itens=data['itens'],
                total=data['total']
            )
            messagebox.showinfo("Sucesso", "Pedido atualizado com sucesso!")
            self._refresh_pedido_list()
            return True
        except Exception as e:
            log.error(f"Erro ao editar pedido: {e}", exc_info=True)
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao atualizar o pedido:\n{e}")
            return False

    def _handle_delete_pedido(self, pedido_id):
        """Exclui um pedido (após confirmação)."""
        log.info(f"MAIN: Tentativa de exclusão do pedido ID: {pedido_id}")
        if self.pedido_view.show_confirm("Confirmar Exclusão",
                                         "Tem certeza que deseja excluir este pedido?\nEsta ação é irreversível."):
            try:
                self.pedido_model.delete_pedido_transacional(pedido_id)
                messagebox.showinfo("Sucesso", "Pedido excluído com sucesso.")
                self._refresh_pedido_list()
            except Exception as e:
                log.error(f"Erro ao excluir pedido: {e}", exc_info=True)
                messagebox.showerror("Erro ao Excluir", f"Ocorreu um erro ao excluir o pedido:\n{e}")


if __name__ == "__main__":
    # 1. Configura o logging ANTES de tudo
    setup_logging()

    # 2. Inicializa o banco de dados
    log.info("Aplicação iniciada.")
    try:
        db.init_db()
        log.info("Banco de dados inicializado com sucesso.")
    except Exception as e:
        log.critical(f"Falha ao inicializar o banco de dados: {e}", exc_info=True)
        messagebox.showerror("Erro Crítico de DB", f"Não foi possível iniciar o banco de dados:\n{e}")
        sys.exit(1)

    # 3. Inicia a aplicação
    app = MainApplication()
    app.mainloop()

