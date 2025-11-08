import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import db
import models
import utils
from views.clientes_view import ClientesViewFrame, ClienteForm
from views.pedidos_view import PedidosViewFrame, PedidoForm
from typing import Optional, Dict, Any, List
import sqlite3  # Para capturar 'IntegrityError'
import export_utils  # Para exportação


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- Configuração da Janela Principal ---
        self.title("Sistema de Clientes e Pedidos")
        self.geometry("900x600")  # Tamanho inicial
        utils.center_window(self)  # Centraliza na tela

        # --- Configuração do Estilo (Tema 'clam') ---
        # Traz um visual mais moderno e consistente
        style = ttk.Style(self)
        style.theme_use('clam')

        # Ajustes finos no estilo (opcional, mas melhora a aparência)
        style.configure("TNotebook.Tab", padding=[12, 5], font=("-size 10"))
        style.configure("TButton", padding=5, font=("-size 10"))
        style.configure("Treeview.Heading", font=("-size 10 -weight bold"))

        # --- Variáveis de Referência (para Views) ---
        self.clientes_view_frame: Optional[ClientesViewFrame] = None
        self.pedidos_view_frame: Optional[PedidosViewFrame] = None

        # --- Inicialização dos Widgets ---
        self.create_widgets()

        # --- Carregamento Inicial de Dados ---
        self.load_clientes_data()
        self.load_pedidos_data()  # Carrega os pedidos

    def create_widgets(self):
        """Cria a estrutura principal (Notebook com abas)."""

        # Frame principal com padding
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill="both", expand=True)

        # --- Notebook (Abas) ---
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # --- Aba de Clientes ---
        # Frame que contém tudo na aba de clientes
        clientes_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(clientes_tab_frame, text="Clientes")

        # Instancia a View de Clientes (a lista)
        # Passamos os 'callbacks' (funções) que a view deve chamar
        self.clientes_view_frame = ClientesViewFrame(
            master=clientes_tab_frame,
            on_open_new_callback=self.open_cliente_form,
            on_open_edit_callback=self.open_cliente_form,  # Reutiliza a mesma função
            on_delete_callback=self.delete_cliente,
            on_search_callback=self.load_clientes_data  # 'Buscar' recarrega a lista com o filtro
        )
        self.clientes_view_frame.pack(fill="both", expand=True)

        # --- Aba de Pedidos ---
        pedidos_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(pedidos_tab_frame, text="Pedidos")

        # Botão "Novo Pedido" (fica *acima* da lista de pedidos)
        # (Design diferente da aba Clientes, onde o botão 'Novo' está junto da busca)
        novo_pedido_button = ttk.Button(pedidos_tab_frame,
                                        text="Criar Novo Pedido",
                                        command=self.open_pedido_form)
        novo_pedido_button.pack(anchor="ne", pady=(0, 10))  # Alinhado à direita (Nordeste)

        # Instancia a View de Pedidos (a lista)
        self.pedidos_view_frame = PedidosViewFrame(
            master=pedidos_tab_frame,
            on_delete_callback=self.delete_pedido,
            on_search_callback=self.load_pedidos_data,  # 'Buscar' recarrega com filtros
            on_clear_filters_callback=self.load_pedidos_data,  # 'Limpar' recarrega tudo
            on_export_csv_callback=self.export_pedido_csv,
            on_export_pdf_callback=self.export_pedido_pdf
        )
        self.pedidos_view_frame.pack(fill="both", expand=True)

    # =========================================================================
    # === MÉTODOS CONTROLADORES (LÓGICA) - CLIENTES ===
    # =========================================================================

    def load_clientes_data(self, search_term: str = ""):
        """
        Busca dados no 'models' e atualiza a 'view' de clientes.
        """
        try:
            # 1. Busca dados no Model
            # CORREÇÃO: Chamando o nome correto 'get_clientes_data'
            clientes_list = models.get_clientes_data(search_term)

            # 2. Atualiza a View (Treeview)
            if self.clientes_view_frame:
                self.clientes_view_frame.refresh_data(clientes_list)

        except Exception as e:
            print(f"ERRO [main.load_clientes_data]: {e}")
            messagebox.showerror("Erro ao Carregar Clientes",
                                 f"Não foi possível carregar os dados dos clientes:\n{e}",
                                 parent=self)

    def open_cliente_form(self, cliente_data: Optional[Dict[str, Any]] = None):
        """
        Abre o popup (Toplevel) ClienteForm para Novo ou Edição.

        :param cliente_data: Se None, abre em modo 'Novo'.
                             Se Dict, abre em modo 'Editar'.
        """
        ClienteForm(
            master=self,
            on_save_callback=self.save_cliente,
            on_cancel_callback=self.on_form_cancel,
            cliente=cliente_data  # Passa os dados (ou None)
        )

    def save_cliente(self, cliente_data: Dict[str, Any]):
        """
        Recebe os dados do ClienteForm e manda para o 'models' salvar.
        """
        try:
            # 1. Manda para o Model salvar
            models.save_cliente(cliente_data)

            # 2. Recarrega os dados (para a lista e comboboxes)
            self.load_clientes_data()

            # (Se a view de pedidos estiver visível, talvez recarregar os clientes
            # do combobox dela, mas isso é uma melhoria futura)

            id_str = cliente_data.get('id', 'Novo')
            print(f"INFO [main]: Cliente ID {id_str} salvo com sucesso.")

        except sqlite3.IntegrityError as e:
            # Erro específico para 'UNIQUE constraint failed'
            if "UNIQUE constraint failed: clientes.email" in str(e):
                print(f"ERRO [main.save_cliente]: Email duplicado.")
                messagebox.showerror("Erro ao Salvar",
                                     f"O e-mail '{cliente_data['email']}' já está cadastrado.",
                                     parent=self)
            else:
                print(f"ERRO [main.save_cliente] (Integrity): {e}")
                messagebox.showerror("Erro de Banco de Dados",
                                     f"Erro de integridade ao salvar:\n{e}",
                                     parent=self)
            raise e  # Re-levanta o erro para o form não fechar

        except Exception as e:
            print(f"ERRO [main.save_cliente]: {e}")
            messagebox.showerror("Erro ao Salvar",
                                 f"Ocorreu um erro inesperado ao salvar o cliente:\n{e}",
                                 parent=self)
            raise e  # Re-levanta o erro para o form não fechar

    def delete_cliente(self, cliente_id: int):
        """
        Recebe o ID da ClientesViewFrame e manda para o 'models' excluir.
        """
        try:
            # 1. Manda para o Model excluir
            models.delete_cliente(cliente_id)

            # 2. Recarrega os dados
            self.load_clientes_data()

            print(f"INFO [main]: Cliente ID {cliente_id} excluído com sucesso.")

        except sqlite3.IntegrityError as e:
            # Erro específico 'FOREIGN KEY constraint failed'
            if "FOREIGN KEY constraint failed" in str(e):
                print(f"ERRO [main.delete_cliente]: Cliente com pedidos.")
                messagebox.showerror("Erro ao Excluir",
                                     f"Este cliente não pode ser excluído pois possui pedidos associados.",
                                     parent=self)
            else:
                print(f"ERRO [main.delete_cliente] (Integrity): {e}")
                messagebox.showerror("Erro de Banco de Dados",
                                     f"Erro de integridade ao excluir:\n{e}",
                                     parent=self)

        except Exception as e:
            print(f"ERRO [main.delete_cliente]: {e}")
            messagebox.showerror("Erro ao Excluir",
                                 f"Ocorreu um erro inesperado ao excluir o cliente:\n{e}",
                                 parent=self)

    def on_form_cancel(self):
        """Callback genérico para quando um formulário é cancelado."""
        print("Formulário cancelado.")

    # =========================================================================
    # === MÉTODOS CONTROLADORES (LÓGICA) - PEDIDOS ===
    # =========================================================================

    def load_pedidos_data(self, search_term: str = "", date_start: str = "", date_end: str = ""):
        """
        Busca dados no 'models' e atualiza a 'view' de pedidos.
        """
        try:
            # 1. Busca dados no Model
            # CORREÇÃO: Chamando a nova função 'get_filtered_pedidos_data'
            pedidos_list = models.get_filtered_pedidos_data(search_term, date_start, date_end)

            # 2. Atualiza a View (Treeview)
            if self.pedidos_view_frame:
                self.pedidos_view_frame.refresh_data(pedidos_list)

        except Exception as e:
            print(f"ERRO [main.load_pedidos_data]: {e}")
            messagebox.showerror("Erro ao Carregar Pedidos",
                                 f"Não foi possível carregar os dados dos pedidos:\n{e}",
                                 parent=self)

    def open_pedido_form(self):
        """
        Abre o popup (Toplevel) PedidoForm para um Novo Pedido.
        """
        try:
            # 1. Busca os clientes para o Combobox
            # CORREÇÃO: Chamando 'get_clientes_combobox_data'
            clientes_list = models.get_clientes_combobox_data()

            if not clientes_list:
                messagebox.showinfo("Aviso",
                                    "Não é possível criar um pedido pois não há clientes cadastrados.",
                                    parent=self)
                return

            # 2. Abre o formulário
            PedidoForm(
                master=self,
                on_save_callback=self.save_pedido,
                on_cancel_callback=self.on_form_cancel,
                clientes_combobox_data=clientes_list  # Passa a lista
            )

        except Exception as e:
            print(f"ERRO [main.open_pedido_form]: {e}")
            messagebox.showerror("Erro ao Abrir Formulário",
                                 f"Não foi possível carregar os dados para o formulário de pedido:\n{e}",
                                 parent=self)

    def save_pedido(self, pedido_data: Dict[str, Any], itens_list: List[Dict[str, Any]]):
        """
        Recebe os dados do PedidoForm e manda para o 'models' salvar (transação).
        """
        try:
            # 1. Manda para o Model salvar (transação)
            models.save_pedido(pedido_data, itens_list)

            # 2. Recarrega a lista de pedidos
            self.load_pedidos_data()

            print(f"INFO [main]: Novo pedido salvo com sucesso.")

        except Exception as e:
            # Captura qualquer erro da transação (ex: falha ao inserir item)
            print(f"ERRO [main.save_pedido]: {e}")
            messagebox.showerror("Erro ao Salvar Pedido",
                                 f"Ocorreu um erro inesperado ao salvar o pedido:\n{e}",
                                 parent=self)
            raise e  # Re-levanta o erro para o form não fechar

    def delete_pedido(self, pedido_id: int):
        """
        Recebe o ID da PedidosViewFrame e manda para o 'models' excluir.
        """
        try:
            # 1. Manda para o Model excluir
            models.delete_pedido(pedido_id)

            # 2. Recarrega os dados
            self.load_pedidos_data()

            print(f"INFO [main]: Pedido ID {pedido_id} excluído com sucesso.")

        except Exception as e:
            print(f"ERRO [main.delete_pedido]: {e}")
            messagebox.showerror("Erro ao Excluir Pedido",
                                 f"Ocorreu um erro inesperado ao excluir o pedido:\n{e}",
                                 parent=self)

    # =========================================================================
    # === MÉTODOS CONTROLADORES (LÓGICA) - EXPORTAÇÃO ===
    # =========================================================================

    def export_pedido_csv(self, pedido_id: int):
        """Lógica para exportar um único pedido para CSV."""
        print(f"INFO [main]: Solicitada exportação CSV para Pedido ID {pedido_id}")
        try:
            # 1. Obter os dados detalhados
            pedido_info, itens_list = models.get_pedido_details(pedido_id)

            # 2. Chamar o utilitário de exportação
            filepath = export_utils.export_to_csv(pedido_info, itens_list)

            if filepath:
                messagebox.showinfo("Exportação Concluída",
                                    f"Pedido exportado para CSV com sucesso:\n{filepath}",
                                    parent=self)
        except Exception as e:
            print(f"ERRO [main.export_pedido_csv]: {e}")
            messagebox.showerror("Erro na Exportação",
                                 f"Ocorreu um erro ao gerar o arquivo CSV:\n{e}",
                                 parent=self)

    def export_pedido_pdf(self, pedido_id: int):
        """Lógica para exportar um único pedido para PDF."""
        print(f"INFO [main]: Solicitada exportação PDF para Pedido ID {pedido_id}")
        try:
            # 1. Obter os dados detalhados
            pedido_info, itens_list = models.get_pedido_details(pedido_id)

            # 2. Chamar o utilitário de exportação
            filepath = export_utils.export_to_pdf(pedido_info, itens_list)

            if filepath:
                messagebox.showinfo("Exportação Concluída",
                                    f"Pedido exportado para PDF com sucesso:\n{filepath}",
                                    parent=self)
        except Exception as e:
            print(f"ERRO [main.export_pedido_pdf]: {e}")
            messagebox.showerror("Erro na Exportação",
                                 f"Ocorreu um erro ao gerar o arquivo PDF:\n{e}",
                                 parent=self)


if __name__ == "__main__":
    try:
        print("Inicializando banco de dados...")
        db.init_db()
    except Exception as e:
        print(f"ERRO FATAL: Não foi possível inicializar o banco de dados: {e}")
        messagebox.showerror("Erro Crítico de Banco de Dados",
                             f"Não foi possível inicializar o banco de dados: {e}\n\nO aplicativo será fechado.")
        exit(1)  # Sai se o DB não puder ser iniciado

    app = App()
    app.mainloop()