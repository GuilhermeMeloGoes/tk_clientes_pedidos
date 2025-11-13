"""
Main.py (Controlador)

Este é o ponto de entrada principal do aplicativo.
Ele inicializa a janela raiz do Tkinter e age como o "controlador"
(na arquitetura MVC), conectando a lógica (Models) com a
interface (Views).

Esta versão usa um Menu Bar superior e gerencia as telas (frames)
em vez de usar um Notebook (abas).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List, Tuple
import datetime
import threading  # Para a análise de IA

# Importa as camadas
import db
import models
import utils
import export_utils
import app_logger

# Importa as classes de View
from views.dashboard_view import DashboardFrame
from views.clientes_view import ClientesViewFrame, ClienteForm
from views.pedidos_view import PedidosViewFrame, PedidoForm
from views.relatorios_view import RelatoriosViewFrame
from views.historico_view import HistoricoViewFrame


# =============================================================================
# === CLASSE PRINCIPAL DA APLICAÇÃO (CONTROLADOR) ===
# =============================================================================

class App(tk.Tk):
    """
    Classe principal da aplicação, herdando de tk.Tk.
    Gerencia a janela principal, o Menu Bar e a troca de frames (telas).
    """

    def __init__(self):
        super().__init__()

        # --- Configuração do Tema (DEVE ser a primeira coisa) ---
        self.style = ttk.Style(self)
        self.is_dark_theme = False  # Começa no tema claro
        utils.setup_light_theme(self.style)

        # --- Configuração da Janela ---
        self.title("Sistema de Clientes e Pedidos")
        self.geometry("1000x700")  # Tamanho inicial
        self.minsize(900, 600)

        # --- Estado da Aplicação ---
        # Rastreia qual formulário (ClienteForm, PedidoForm) está aberto
        # e se ele tem dados não salvos ("dirty")
        self.current_open_form: Optional[tk.Toplevel] = None
        self.is_form_dirty: bool = False

        # Intercepta o botão 'X' da janela principal
        self.protocol("WM_DELETE_WINDOW", self.on_close_app)

        # --- Inicialização do Banco de Dados ---
        try:
            print("Inicializando banco de dados...")
            db.init_db()
        except Exception as e:
            messagebox.showerror("Erro Fatal de Banco de Dados",
                                 f"Não foi possível inicializar o banco de dados: {e}\n"
                                 "A aplicação será fechada.")
            self.destroy()
            return

        # --- Dados em Cache (para Comboboxes) ---
        self.clientes_combobox_list: List[Tuple] = []

        # --- Cria os Widgets (Menu e Frames) ---
        self.frames: Dict[str, ttk.Frame] = {}
        self.create_menu()
        self.create_frames_container()
        self.create_all_frames()

        # --- Carrega Dados Iniciais ---
        self.load_initial_data()

        # Mostra a tela inicial (Dashboard)
        self.show_frame("Dashboard")

    def create_menu(self):
        """Cria e anexa o Menu Bar principal."""

        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # --- Menu "Navegação" ---
        nav_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Navegar", menu=nav_menu)
        nav_menu.add_command(label="Dashboard", command=lambda: self.show_frame("Dashboard"))
        nav_menu.add_separator()
        nav_menu.add_command(label="Clientes", command=lambda: self.show_frame("Clientes"))
        nav_menu.add_command(label="Pedidos", command=lambda: self.show_frame("Pedidos"))
        nav_menu.add_command(label="Relatórios", command=lambda: self.show_frame("Relatorios"))
        nav_menu.add_command(label="Histórico", command=lambda: self.show_frame("Historico"))
        nav_menu.add_separator()
        nav_menu.add_command(label="Sair", command=self.on_close_app)

        # --- Menu "Ações" (CORRIGIDO) ---
        actions_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Ações", menu=actions_menu)
        actions_menu.add_command(label="Novo Cliente...", command=lambda: self.open_cliente_form(None))
        actions_menu.add_command(label="Novo Pedido...", command=self.open_pedido_form)

        # --- Menu "Análise" ---
        analysis_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Análise", menu=analysis_menu)
        analysis_menu.add_command(label="Analisar Pedidos (IA)", command=self.start_analysis_thread)

        # --- Menu "Opções" ---
        options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Opções", menu=options_menu)
        options_menu.add_command(label="Alternar Tema (Claro/Escuro)", command=self.toggle_theme)

    def create_frames_container(self):
        """Cria o container principal onde os frames (telas) serão empilhados."""

        self.container = ttk.Frame(self, padding="10 10 10 10")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def create_all_frames(self):
        """
        Inicializa todas as classes de 'View' (telas) e as
        armazena no dicionário self.frames.
        """

        try:
            self.clientes_combobox_list = models.get_clientes_combobox_data()
        except Exception as e:
            print(f"ERRO [main.create_all_frames]: {e}")
            messagebox.showerror("Erro ao Carregar", f"Não foi possível buscar a lista de clientes:\n{e}", parent=self)
            self.clientes_combobox_list = []

        # Itera e cria cada frame
        for FrameClass, frame_name in [
            (DashboardFrame, "Dashboard"),
            (ClientesViewFrame, "Clientes"),
            (PedidosViewFrame, "Pedidos"),
            (RelatoriosViewFrame, "Relatorios"),
            (HistoricoViewFrame, "Historico")
        ]:

            kwargs = {"master": self.container}

            if frame_name == "Dashboard":
                kwargs["on_refresh_callback"] = self.load_dashboard_data
                kwargs["on_analyze_callback"] = self.start_analysis_thread

            elif frame_name == "Clientes":
                kwargs["on_new_callback"] = self.open_cliente_form
                kwargs["on_edit_callback"] = self.open_cliente_form
                kwargs["on_delete_callback"] = self.delete_cliente
                kwargs["on_search_callback"] = self.load_clientes_data

            elif frame_name == "Pedidos":
                # CORREÇÃO: Adiciona o callback para o novo botão
                kwargs["on_new_callback"] = self.open_pedido_form
                kwargs["on_delete_callback"] = self.delete_pedido
                kwargs["on_search_callback"] = self.load_pedidos_data
                kwargs["on_clear_filters_callback"] = self.load_pedidos_data
                kwargs["on_export_csv_callback"] = self.export_pedido_csv
                kwargs["on_export_pdf_callback"] = self.export_pedido_pdf

            elif frame_name == "Relatorios":
                kwargs["clientes_combobox_data"] = self.clientes_combobox_list
                kwargs["on_search_callback"] = self.load_relatorios_data
                kwargs["on_clear_filters_callback"] = self.load_relatorios_data
                kwargs["on_export_csv_callback"] = self.export_relatorio_csv
                kwargs["on_export_pdf_callback"] = self.export_relatorio_pdf

            elif frame_name == "Historico":
                kwargs["on_refresh_callback"] = self.load_historico_data
                kwargs["on_clear_callback"] = self.clear_historico_data

            # Cria a instância do frame
            frame = FrameClass(**kwargs)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name: str):
        """Traz um frame (tela) para a frente."""
        print(f"INFO [main]: Mostrando frame: {frame_name}")
        frame = self.frames[frame_name]
        frame.tkraise()  # Traz o frame para o topo

    def load_initial_data(self):
        """Carrega os dados de todas as telas na inicialização."""
        print("Carregando dados iniciais...")
        self.load_dashboard_data(show_success=False)
        self.load_clientes_data()
        self.load_pedidos_data()
        self.load_relatorios_data()
        self.load_historico_data()

    def on_close_app(self):
        """
        Chamado ao fechar a janela (no 'X' ou 'Sair').
        Verifica se há formulários abertos com dados não salvos.
        """
        if self.current_open_form and self.is_form_dirty:
            if messagebox.askyesno("Descartar Alterações?",
                                   "Você tem um formulário aberto com alterações que não foram salvas. "
                                   "Deseja fechar o aplicativo e descartar tudo?",
                                   parent=self.current_open_form):
                print("INFO [main]: Fechando app e descartando alterações.")
                self.destroy()
            else:
                print("INFO [main]: Fechamento do app cancelado.")
                return
        else:
            print("INFO [main]: Fechando app.")
            self.destroy()

    # =============================================================================
    # === LÓGICA DE TEMAS (CLARO/ESCURO) ===
    # =============================================================================

    def toggle_theme(self):
        """Alterna entre o tema claro e escuro."""
        self.is_dark_theme = not self.is_dark_theme

        if self.is_dark_theme:
            print("INFO [main]: Mudando para Tema Escuro")
            utils.setup_dark_theme(self.style)
        else:
            print("INFO [main]: Mudando para Tema Claro")
            utils.setup_light_theme(self.style)

        # Atualiza os widgets não-ttk (ScrolledText e Labels dos Cards)
        try:
            self.frames["Historico"].update_theme(self.is_dark_theme)
            self.frames["Dashboard"].update_theme(self.is_dark_theme)
        except Exception as e:
            print(f"ERRO [main.toggle_theme]: Não foi possível atualizar o tema customizado: {e}")

    # =============================================================================
    # === LÓGICA DO DASHBOARD (CONTROLADOR) ===
    # =============================================================================

    def load_dashboard_data(self, show_success: bool = True):
        """ Busca os dados do Dashboard no 'models' e atualiza a 'view'. """
        print("INFO [main]: Atualizando dados do Dashboard...")
        self.frames["Dashboard"].set_loading_state(True)
        try:
            stats = models.get_dashboard_stats()
            self.frames["Dashboard"].update_stats(stats)
            if show_success:
                messagebox.showinfo("Sucesso", "Dados do Dashboard atualizados.", parent=self)
        except Exception as e:
            print(f"ERRO [main.load_dashboard_data]: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os dados do Dashboard:\n{e}", parent=self)
            self.frames["Dashboard"].update_stats({})
        finally:
            self.frames["Dashboard"].set_loading_state(False)

    # =============================================================================
    # === LÓGICA DE CLIENTES (CONTROLADOR) ===
    # =============================================================================

    def load_clientes_data(self, search_term: str = ""):
        """ Busca os dados dos clientes no 'models' e atualiza a 'view'. """
        try:
            clientes_list = models.get_clientes_data(search_term)
            self.frames["Clientes"].refresh_data(clientes_list)
        except Exception as e:
            print(f"ERRO [main.load_clientes_data]: {e}")
            messagebox.showerror("Erro ao Carregar Clientes", f"Não foi possível buscar os dados dos clientes:\n{e}",
                                 parent=self)

    def open_cliente_form(self, cliente_data: Optional[Dict[str, Any]] = None):
        """ Abre o formulário ClienteForm (Toplevel) para Novo ou Editar. """

        if self.current_open_form:
            self.current_open_form.focus_set()
            return

        self.frames["Clientes"].new_button.config(state="disabled")
        self.frames["Clientes"].edit_button.config(state="disabled")
        self.frames["Clientes"].delete_button.config(state="disabled")

        self.current_open_form = ClienteForm(
            master=self,
            on_save_callback=self.save_cliente,
            on_cancel_callback=self.on_form_cancel,
            on_dirty_callback=self.on_form_dirty,  # Rastreia "não salvo"
            cliente_data=cliente_data
        )

    def save_cliente(self, cliente_data: Dict[str, Any]):
        """ Salva o cliente e registra no log. """
        try:
            action = "atualizado" if cliente_data.get('id') else "criado"
            nome_cliente = cliente_data.get('nome')

            models.save_cliente(cliente_data)
            app_logger.log_action(f"Cliente {action}: '{nome_cliente}' (ID: {cliente_data.get('id', 'Novo')})")
            messagebox.showinfo("Sucesso", f"Cliente {action} com sucesso!", parent=self)

            # Recarrega dados
            self.load_clientes_data()
            self.clientes_combobox_list = models.get_clientes_combobox_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.save_cliente]: {e}")
            messagebox.showerror("Erro ao Salvar Cliente", f"Não foi possível salvar o cliente:\n{e}", parent=self)
            raise e  # Re-levanta o erro para o form

    def delete_cliente(self, cliente_id: int):
        """ Exclui o cliente e registra no log. """
        try:
            models.delete_cliente(cliente_id)
            app_logger.log_action(f"Cliente excluído: ID {cliente_id}")
            messagebox.showinfo("Sucesso", "Cliente excluído com sucesso!", parent=self)

            self.load_clientes_data()
            self.clientes_combobox_list = models.get_clientes_combobox_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.delete_cliente]: {e}")
            if "FOREIGN KEY constraint failed" in str(e):
                messagebox.showerror("Erro ao Excluir Cliente",
                                     "Não é possível excluir este cliente pois ele está associado a um ou mais pedidos.",
                                     parent=self)
            else:
                messagebox.showerror("Erro ao Excluir Cliente", f"Não foi possível excluir o cliente:\n{e}",
                                     parent=self)

    def on_form_cancel(self):
        """ Callback que os formulários chamam ao fechar. """
        # Reativa os botões
        self.frames["Clientes"].new_button.config(state="normal")
        self.frames["Clientes"].edit_button.config(state="normal")
        self.frames["Clientes"].delete_button.config(state="normal")
        # CORREÇÃO: Reativa o botão na tela de Pedidos
        self.frames["Pedidos"].new_button.config(state="normal")

        self.current_open_form = None
        self.is_form_dirty = False
        print("Formulário cancelado.")

    def on_form_dirty(self, form_instance: tk.Toplevel):
        """ Callback que os formulários chamam QUANDO o usuário digita algo. """
        if self.current_open_form == form_instance:
            self.is_form_dirty = True
            print("INFO [main]: Formulário marcado como 'dirty'.")

    # =============================================================================
    # === LÓGICA DE PEDIDOS (CONTROLADOR) ===
    # =============================================================================

    def load_pedidos_data(self, search_term: str = "", date_start: str = "", date_end: str = ""):
        """ Busca os dados dos pedidos no 'models' (com filtros) e atualiza a 'view'. """
        try:
            pedidos_list = models.get_filtered_pedidos_data(search_term, date_start, date_end)
            self.frames["Pedidos"].refresh_data(pedidos_list)
        except Exception as e:
            print(f"ERRO [main.load_pedidos_data]: {e}")
            messagebox.showerror("Erro ao Carregar Pedidos", f"Não foi possível buscar os dados dos pedidos:\n{e}",
                                 parent=self)

    def open_pedido_form(self):
        """ Abre o formulário PedidoForm (Toplevel) para um Novo Pedido. """

        if self.current_open_form:
            self.current_open_form.focus_set()
            return

        if not self.clientes_combobox_list:
            messagebox.showwarning("Sem Clientes", "Não é possível criar um pedido pois não há clientes cadastrados.",
                                   parent=self)
            return

        # CORREÇÃO: Desativa o botão na tela de Pedidos
        self.frames["Pedidos"].new_button.config(state="disabled")

        self.current_open_form = PedidoForm(
            master=self,
            on_save_callback=self.save_pedido,
            on_cancel_callback=self.on_form_cancel,
            on_dirty_callback=self.on_form_dirty,  # Rastreia "não salvo"
            clientes_combobox_data=self.clientes_combobox_list
        )

    def save_pedido(self, pedido_data: Dict[str, Any], itens_data: List[Dict[str, Any]]):
        """ Salva o pedido e registra no log. """
        try:
            models.save_pedido(pedido_data, itens_data)
            app_logger.log_action(
                f"Novo Pedido criado: Cliente ID {pedido_data.get('cliente_id')}, Total R$ {pedido_data.get('total')}")
            messagebox.showinfo("Sucesso", "Pedido criado com sucesso!", parent=self)

            self.load_pedidos_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.save_pedido]: {e}")
            messagebox.showerror("Erro ao Salvar Pedido", f"Não foi possível salvar o pedido:\n{e}", parent=self)
            raise e  # Re-levanta o erro para o form

    def delete_pedido(self, pedido_id: int):
        """ Exclui o pedido e registra no log. """
        try:
            models.delete_pedido(pedido_id)
            app_logger.log_action(f"Pedido excluído: ID {pedido_id}")
            messagebox.showinfo("Sucesso", "Pedido excluído com sucesso!", parent=self)

            self.load_pedidos_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.delete_pedido]: {e}")
            messagebox.showerror("Erro ao Excluir Pedido", f"Não foi possível excluir o pedido:\n{e}", parent=self)

    # =============================================================================
    # === LÓGICA DE EXPORTAÇÃO (PEDIDO ÚNICO) ===
    # =============================================================================

    def export_pedido_csv(self, pedido_id: int):
        """Exporta um pedido selecionado para CSV."""
        print(f"INFO [main]: Solicitada exportação CSV para Pedido ID {pedido_id}")
        try:
            pedido_info, itens_list = models.get_pedido_details(pedido_id)
            if not pedido_info:
                messagebox.showerror("Erro", f"Pedido ID {pedido_id} não encontrado.", parent=self)
                return
            filepath = export_utils.export_to_csv(pedido_info, itens_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Pedido exportado para CSV com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_pedido_csv]: {e}")
            messagebox.showerror("Erro na Exportação CSV", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    def export_pedido_pdf(self, pedido_id: int):
        """Exporta um pedido selecionado para PDF."""
        print(f"INFO [main]: Solicitada exportação PDF para Pedido ID {pedido_id}")
        try:
            pedido_info, itens_list = models.get_pedido_details(pedido_id)
            if not pedido_info:
                messagebox.showerror("Erro", f"Pedido ID {pedido_id} não encontrado.", parent=self)
                return
            filepath = export_utils.export_to_pdf(pedido_info, itens_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Pedido exportado para PDF com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_pedido_pdf]: {e}")
            messagebox.showerror("Erro na Exportação PDF", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    # =============================================================================
    # === LÓGICA DE RELATÓRIOS ===
    # =============================================================================

    def load_relatorios_data(self, cliente_id: str = "", date_start: str = "", date_end: str = ""):
        """ Busca os dados para o Relatório no 'models' (com filtros) e atualiza a 'view'. """
        try:
            relatorios_list = models.get_report_data(cliente_id, date_start, date_end)
            self.frames["Relatorios"].refresh_data(relatorios_list)
        except Exception as e:
            print(f"ERRO [main.load_relatorios_data]: {e}")
            messagebox.showerror("Erro ao Carregar Relatório", f"Não foi possível buscar os dados do relatório:\n{e}",
                                 parent=self)

    def export_relatorio_csv(self, data_list: List[Tuple]):
        """Exporta a lista (já filtrada) da aba Relatórios para CSV."""
        print(f"INFO [main]: Solicitada exportação CSV para lista de Relatório")
        try:
            filepath = export_utils.export_list_to_csv(data_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Relatório exportado para CSV com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_relatorio_csv]: {e}")
            messagebox.showerror("Erro na Exportação CSV", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    def export_relatorio_pdf(self, data_list: List[Tuple]):
        """Exporta a lista (já filtrada) da aba Relatórios para PDF."""
        print(f"INFO [main]: Solicitada exportação PDF para lista de Relatório")
        try:
            filepath = export_utils.export_list_to_pdf(data_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Relatório exportado para PDF com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_relatorio_pdf]: {e}")
            messagebox.showerror("Erro na Exportação PDF", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    # =============================================================================
    # === LÓGICA DE ANÁLISE IA ===
    # =============================================================================

    def start_analysis_thread(self):
        """
        Inicia a análise de IA em uma thread separada
        para não bloquear a interface principal (GUI).
        """
        print("INFO [main]: Iniciando thread de análise de IA...")

        # Passa 'daemon=True' para que a thread
        # não impeça o aplicativo de fechar.
        ia_thread = threading.Thread(target=self._run_ia_analysis, daemon=True)
        ia_thread.start()

    def _run_ia_analysis(self):
        """
        Função que roda na thread.
        Chama o 'utils' para fazer a análise (que é demorada)
        e atualiza a UI com o resultado.
        """
        try:
            # 1. Coloca a UI em modo "carregando"
            self.frames["Dashboard"].set_analysis_state(True)

            # 2. Chama a função bloqueante (utils)
            print("INFO [main._run_ia_analysis]: Chamando utils.analisar_pedidos_ia()...")
            resposta_ia = utils.analisar_pedidos_ia()

            # 3. Atualiza a UI com o resultado
            self.frames["Dashboard"].set_analysis_result(resposta_ia)

        except Exception as e:
            # Pega qualquer erro inesperado na thread
            print(f"ERRO [main._run_ia_analysis]: Falha crítica na thread de IA: {e}")
            erro_msg = f"Ocorreu um erro inesperado durante a análise:\n{e}"
            self.frames["Dashboard"].set_analysis_result(erro_msg)

        finally:
            # 4. Garante que a UI volte ao estado normal
            self.frames["Dashboard"].set_analysis_state(False)
            print("INFO [main._run_ia_analysis]: Thread de análise finalizada.")

    # =============================================================================
    # === LÓGICA DE HISTÓRICO ===
    # =============================================================================

    def load_historico_data(self):
        """ Busca o conteúdo do log no 'app_logger' e atualiza a 'view'. """
        print("INFO [main]: Carregando histórico de logs...")
        try:
            self.frames["Historico"].set_loading_state(True)
            log_content = app_logger.read_log()
            self.frames["Historico"].set_log_content(log_content)
        except Exception as e:
            print(f"ERRO [main.load_historico_data]: {e}")
            messagebox.showerror("Erro ao Carregar Histórico", f"Não foi possível ler o arquivo de log:\n{e}",
                                 parent=self)
            self.frames["Historico"].set_log_content(f"ERRO: {e}")
        finally:
            self.frames["Historico"].set_loading_state(False)

    def clear_historico_data(self):
        """ Pede confirmação e limpa o arquivo de log. """
        print("INFO [main]: Solicitação para limpar histórico.")
        if not messagebox.askyesno("Confirmar Limpeza",
                                   "Tem certeza que deseja limpar todo o histórico de ações?\n\n"
                                   "Esta ação não pode ser desfeita.",
                                   parent=self, icon="warning"):
            return
        try:
            self.frames["Historico"].set_loading_state(True)
            app_logger.clear_log()
            self.load_historico_data()  # Recarrega (mostrará "Histórico limpo")
            messagebox.showinfo("Sucesso", "Histórico de logs limpo com sucesso.", parent=self)
        except Exception as e:
            print(f"ERRO [main.clear_historico_data]: {e}")
            messagebox.showerror("Erro ao Limpar", f"Não foi possível limpar o arquivo de log:\n{e}", parent=self)
        finally:
            self.frames["Historico"].set_loading_state(False)


# =============================================================================
# === PONTO DE ENTRADA (EXECUÇÃO) ===
# =============================================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()
    """
    Main.py (Controlador)
    
    Este é o ponto de entrada principal do aplicativo.
    Ele inicializa a janela raiz do Tkinter e age como o "controlador"
    (na arquitetura MVC), conectando a lógica (Models) com a
    interface (Views).
    
    Esta versão usa um Menu Bar superior e gerencia as telas (frames)
    em vez de usar um Notebook (abas).
    """

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List, Tuple
import datetime
import threading  # Para a análise de IA

# Importa as camadas
import db
import models
import utils
import export_utils
import app_logger

# Importa as classes de View
from views.dashboard_view import DashboardFrame
from views.clientes_view import ClientesViewFrame, ClienteForm
from views.pedidos_view import PedidosViewFrame, PedidoForm
from views.relatorios_view import RelatoriosViewFrame
from views.historico_view import HistoricoViewFrame


# =============================================================================
# === CLASSE PRINCIPAL DA APLICAÇÃO (CONTROLADOR) ===
# =============================================================================

class App(tk.Tk):
    """
    Classe principal da aplicação, herdando de tk.Tk.
    Gerencia a janela principal, o Menu Bar e a troca de frames (telas).
    """

    def __init__(self):
        super().__init__()

        # --- Configuração do Tema (DEVE ser a primeira coisa) ---
        self.style = ttk.Style(self)
        self.is_dark_theme = False  # Começa no tema claro
        utils.setup_light_theme(self.style)

        # --- Configuração da Janela ---
        self.title("Sistema de Clientes e Pedidos")
        self.geometry("1000x700")  # Tamanho inicial
        self.minsize(900, 600)

        # --- Estado da Aplicação ---
        # Rastreia qual formulário (ClienteForm, PedidoForm) está aberto
        # e se ele tem dados não salvos ("dirty")
        self.current_open_form: Optional[tk.Toplevel] = None
        self.is_form_dirty: bool = False

        # Intercepta o botão 'X' da janela principal
        self.protocol("WM_DELETE_WINDOW", self.on_close_app)

        # --- Inicialização do Banco de Dados ---
        try:
            print("Inicializando banco de dados...")
            db.init_db()
        except Exception as e:
            messagebox.showerror("Erro Fatal de Banco de Dados",
                                 f"Não foi possível inicializar o banco de dados: {e}\n"
                                 "A aplicação será fechada.")
            self.destroy()
            return

        # --- Dados em Cache (para Comboboxes) ---
        self.clientes_combobox_list: List[Tuple] = []

        # --- Cria os Widgets (Menu e Frames) ---
        self.frames: Dict[str, ttk.Frame] = {}
        self.create_menu()
        self.create_frames_container()
        self.create_all_frames()

        # --- Carrega Dados Iniciais ---
        self.load_initial_data()

        # Mostra a tela inicial (Dashboard)
        self.show_frame("Dashboard")

    def create_menu(self):
        """Cria e anexa o Menu Bar principal."""

        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # --- Menu "Navegação" ---
        nav_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Navegar", menu=nav_menu)
        nav_menu.add_command(label="Dashboard", command=lambda: self.show_frame("Dashboard"))
        nav_menu.add_separator()
        nav_menu.add_command(label="Clientes", command=lambda: self.show_frame("Clientes"))
        nav_menu.add_command(label="Pedidos", command=lambda: self.show_frame("Pedidos"))
        nav_menu.add_command(label="Relatórios", command=lambda: self.show_frame("Relatorios"))
        nav_menu.add_command(label="Histórico", command=lambda: self.show_frame("Historico"))
        nav_menu.add_separator()
        nav_menu.add_command(label="Sair", command=self.on_close_app)

        # --- Menu "Ações" (CORRIGIDO) ---
        actions_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Ações", menu=actions_menu)
        actions_menu.add_command(label="Novo Cliente...", command=lambda: self.open_cliente_form(None))
        actions_menu.add_command(label="Novo Pedido...", command=self.open_pedido_form)

        # --- Menu "Análise" ---
        analysis_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Análise", menu=analysis_menu)
        analysis_menu.add_command(label="Analisar Pedidos (IA)", command=self.start_analysis_thread)

        # --- Menu "Opções" ---
        options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Opções", menu=options_menu)
        options_menu.add_command(label="Alternar Tema (Claro/Escuro)", command=self.toggle_theme)

    def create_frames_container(self):
        """Cria o container principal onde os frames (telas) serão empilhados."""

        self.container = ttk.Frame(self, padding="10 10 10 10")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def create_all_frames(self):
        """
        Inicializa todas as classes de 'View' (telas) e as
        armazena no dicionário self.frames.
        """

        try:
            self.clientes_combobox_list = models.get_clientes_combobox_data()
        except Exception as e:
            print(f"ERRO [main.create_all_frames]: {e}")
            messagebox.showerror("Erro ao Carregar", f"Não foi possível buscar a lista de clientes:\n{e}", parent=self)
            self.clientes_combobox_list = []

        # Itera e cria cada frame
        for FrameClass, frame_name in [
            (DashboardFrame, "Dashboard"),
            (ClientesViewFrame, "Clientes"),
            (PedidosViewFrame, "Pedidos"),
            (RelatoriosViewFrame, "Relatorios"),
            (HistoricoViewFrame, "Historico")
        ]:

            kwargs = {"master": self.container}

            if frame_name == "Dashboard":
                kwargs["on_refresh_callback"] = self.load_dashboard_data
                kwargs["on_analyze_callback"] = self.start_analysis_thread

            elif frame_name == "Clientes":
                kwargs["on_new_callback"] = self.open_cliente_form
                kwargs["on_edit_callback"] = self.open_cliente_form
                kwargs["on_delete_callback"] = self.delete_cliente
                kwargs["on_search_callback"] = self.load_clientes_data

            elif frame_name == "Pedidos":
                # CORREÇÃO: Adiciona o callback para o novo botão
                kwargs["on_new_callback"] = self.open_pedido_form
                kwargs["on_delete_callback"] = self.delete_pedido
                kwargs["on_search_callback"] = self.load_pedidos_data
                kwargs["on_clear_filters_callback"] = self.load_pedidos_data
                kwargs["on_export_csv_callback"] = self.export_pedido_csv
                kwargs["on_export_pdf_callback"] = self.export_pedido_pdf

            elif frame_name == "Relatorios":
                kwargs["clientes_combobox_data"] = self.clientes_combobox_list
                kwargs["on_search_callback"] = self.load_relatorios_data
                kwargs["on_clear_filters_callback"] = self.load_relatorios_data
                kwargs["on_export_csv_callback"] = self.export_relatorio_csv
                kwargs["on_export_pdf_callback"] = self.export_relatorio_pdf

            elif frame_name == "Historico":
                kwargs["on_refresh_callback"] = self.load_historico_data
                kwargs["on_clear_callback"] = self.clear_historico_data

            # Cria a instância do frame
            frame = FrameClass(**kwargs)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name: str):
        """Traz um frame (tela) para a frente."""
        print(f"INFO [main]: Mostrando frame: {frame_name}")
        frame = self.frames[frame_name]
        frame.tkraise()  # Traz o frame para o topo

    def load_initial_data(self):
        """Carrega os dados de todas as telas na inicialização."""
        print("Carregando dados iniciais...")
        self.load_dashboard_data(show_success=False)
        self.load_clientes_data()
        self.load_pedidos_data()
        self.load_relatorios_data()
        self.load_historico_data()

    def on_close_app(self):
        """
        Chamado ao fechar a janela (no 'X' ou 'Sair').
        Verifica se há formulários abertos com dados não salvos.
        """
        if self.current_open_form and self.is_form_dirty:
            if messagebox.askyesno("Descartar Alterações?",
                                   "Você tem um formulário aberto com alterações que não foram salvas. "
                                   "Deseja fechar o aplicativo e descartar tudo?",
                                   parent=self.current_open_form):
                print("INFO [main]: Fechando app e descartando alterações.")
                self.destroy()
            else:
                print("INFO [main]: Fechamento do app cancelado.")
                return
        else:
            print("INFO [main]: Fechando app.")
            self.destroy()

    # =============================================================================
    # === LÓGICA DE TEMAS (CLARO/ESCURO) ===
    # =============================================================================

    def toggle_theme(self):
        """Alterna entre o tema claro e escuro."""
        self.is_dark_theme = not self.is_dark_theme

        if self.is_dark_theme:
            print("INFO [main]: Mudando para Tema Escuro")
            utils.setup_dark_theme(self.style)
        else:
            print("INFO [main]: Mudando para Tema Claro")
            utils.setup_light_theme(self.style)

        # Atualiza os widgets não-ttk (ScrolledText e Labels dos Cards)
        try:
            self.frames["Historico"].update_theme(self.is_dark_theme)
            self.frames["Dashboard"].update_theme(self.is_dark_theme)
        except Exception as e:
            print(f"ERRO [main.toggle_theme]: Não foi possível atualizar o tema customizado: {e}")

    # =============================================================================
    # === LÓGICA DO DASHBOARD (CONTROLADOR) ===
    # =============================================================================

    def load_dashboard_data(self, show_success: bool = True):
        """ Busca os dados do Dashboard no 'models' e atualiza a 'view'. """
        print("INFO [main]: Atualizando dados do Dashboard...")
        self.frames["Dashboard"].set_loading_state(True)
        try:
            stats = models.get_dashboard_stats()
            self.frames["Dashboard"].update_stats(stats)
            if show_success:
                messagebox.showinfo("Sucesso", "Dados do Dashboard atualizados.", parent=self)
        except Exception as e:
            print(f"ERRO [main.load_dashboard_data]: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os dados do Dashboard:\n{e}", parent=self)
            self.frames["Dashboard"].update_stats({})
        finally:
            self.frames["Dashboard"].set_loading_state(False)

    # =============================================================================
    # === LÓGICA DE CLIENTES (CONTROLADOR) ===
    # =============================================================================

    def load_clientes_data(self, search_term: str = ""):
        """ Busca os dados dos clientes no 'models' e atualiza a 'view'. """
        try:
            clientes_list = models.get_clientes_data(search_term)
            self.frames["Clientes"].refresh_data(clientes_list)
        except Exception as e:
            print(f"ERRO [main.load_clientes_data]: {e}")
            messagebox.showerror("Erro ao Carregar Clientes", f"Não foi possível buscar os dados dos clientes:\n{e}",
                                 parent=self)

    def open_cliente_form(self, cliente_data: Optional[Dict[str, Any]] = None):
        """ Abre o formulário ClienteForm (Toplevel) para Novo ou Editar. """

        if self.current_open_form:
            self.current_open_form.focus_set()
            return

        self.frames["Clientes"].new_button.config(state="disabled")
        self.frames["Clientes"].edit_button.config(state="disabled")
        self.frames["Clientes"].delete_button.config(state="disabled")

        self.current_open_form = ClienteForm(
            master=self,
            on_save_callback=self.save_cliente,
            on_cancel_callback=self.on_form_cancel,
            on_dirty_callback=self.on_form_dirty,  # Rastreia "não salvo"
            cliente_data=cliente_data
        )

    def save_cliente(self, cliente_data: Dict[str, Any]):
        """ Salva o cliente e registra no log. """
        try:
            action = "atualizado" if cliente_data.get('id') else "criado"
            nome_cliente = cliente_data.get('nome')

            models.save_cliente(cliente_data)
            app_logger.log_action(f"Cliente {action}: '{nome_cliente}' (ID: {cliente_data.get('id', 'Novo')})")
            messagebox.showinfo("Sucesso", f"Cliente {action} com sucesso!", parent=self)

            # Recarrega dados
            self.load_clientes_data()
            self.clientes_combobox_list = models.get_clientes_combobox_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.save_cliente]: {e}")
            messagebox.showerror("Erro ao Salvar Cliente", f"Não foi possível salvar o cliente:\n{e}", parent=self)
            raise e  # Re-levanta o erro para o form

    def delete_cliente(self, cliente_id: int):
        """ Exclui o cliente e registra no log. """
        try:
            models.delete_cliente(cliente_id)
            app_logger.log_action(f"Cliente excluído: ID {cliente_id}")
            messagebox.showinfo("Sucesso", "Cliente excluído com sucesso!", parent=self)

            self.load_clientes_data()
            self.clientes_combobox_list = models.get_clientes_combobox_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.delete_cliente]: {e}")
            if "FOREIGN KEY constraint failed" in str(e):
                messagebox.showerror("Erro ao Excluir Cliente",
                                     "Não é possível excluir este cliente pois ele está associado a um ou mais pedidos.",
                                     parent=self)
            else:
                messagebox.showerror("Erro ao Excluir Cliente", f"Não foi possível excluir o cliente:\n{e}",
                                     parent=self)

    def on_form_cancel(self):
        """ Callback que os formulários chamam ao fechar. """
        # Reativa os botões
        self.frames["Clientes"].new_button.config(state="normal")
        self.frames["Clientes"].edit_button.config(state="normal")
        self.frames["Clientes"].delete_button.config(state="normal")
        # CORREÇÃO: Reativa o botão na tela de Pedidos
        self.frames["Pedidos"].new_button.config(state="normal")

        self.current_open_form = None
        self.is_form_dirty = False
        print("Formulário cancelado.")

    def on_form_dirty(self, form_instance: tk.Toplevel):
        """ Callback que os formulários chamam QUANDO o usuário digita algo. """
        if self.current_open_form == form_instance:
            self.is_form_dirty = True
            print("INFO [main]: Formulário marcado como 'dirty'.")

    # =============================================================================
    # === LÓGICA DE PEDIDOS (CONTROLADOR) ===
    # =============================================================================

    def load_pedidos_data(self, search_term: str = "", date_start: str = "", date_end: str = ""):
        """ Busca os dados dos pedidos no 'models' (com filtros) e atualiza a 'view'. """
        try:
            pedidos_list = models.get_filtered_pedidos_data(search_term, date_start, date_end)
            self.frames["Pedidos"].refresh_data(pedidos_list)
        except Exception as e:
            print(f"ERRO [main.load_pedidos_data]: {e}")
            messagebox.showerror("Erro ao Carregar Pedidos", f"Não foi possível buscar os dados dos pedidos:\n{e}",
                                 parent=self)

    def open_pedido_form(self):
        """ Abre o formulário PedidoForm (Toplevel) para um Novo Pedido. """

        if self.current_open_form:
            self.current_open_form.focus_set()
            return

        if not self.clientes_combobox_list:
            messagebox.showwarning("Sem Clientes", "Não é possível criar um pedido pois não há clientes cadastrados.",
                                   parent=self)
            return

        # CORREÇÃO: Desativa o botão na tela de Pedidos
        self.frames["Pedidos"].new_button.config(state="disabled")

        self.current_open_form = PedidoForm(
            master=self,
            on_save_callback=self.save_pedido,
            on_cancel_callback=self.on_form_cancel,
            on_dirty_callback=self.on_form_dirty,  # Rastreia "não salvo"
            clientes_combobox_data=self.clientes_combobox_list
        )

    def save_pedido(self, pedido_data: Dict[str, Any], itens_data: List[Dict[str, Any]]):
        """ Salva o pedido e registra no log. """
        try:
            models.save_pedido(pedido_data, itens_data)
            app_logger.log_action(
                f"Novo Pedido criado: Cliente ID {pedido_data.get('cliente_id')}, Total R$ {pedido_data.get('total')}")
            messagebox.showinfo("Sucesso", "Pedido criado com sucesso!", parent=self)

            self.load_pedidos_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.save_pedido]: {e}")
            messagebox.showerror("Erro ao Salvar Pedido", f"Não foi possível salvar o pedido:\n{e}", parent=self)
            raise e  # Re-levanta o erro para o form

    def delete_pedido(self, pedido_id: int):
        """ Exclui o pedido e registra no log. """
        try:
            models.delete_pedido(pedido_id)
            app_logger.log_action(f"Pedido excluído: ID {pedido_id}")
            messagebox.showinfo("Sucesso", "Pedido excluído com sucesso!", parent=self)

            self.load_pedidos_data()
            self.load_dashboard_data(show_success=False)
            self.load_historico_data()

        except Exception as e:
            print(f"ERRO [main.delete_pedido]: {e}")
            messagebox.showerror("Erro ao Excluir Pedido", f"Não foi possível excluir o pedido:\n{e}", parent=self)

    # =============================================================================
    # === LÓGICA DE EXPORTAÇÃO (PEDIDO ÚNICO) ===
    # =============================================================================

    def export_pedido_csv(self, pedido_id: int):
        """Exporta um pedido selecionado para CSV."""
        print(f"INFO [main]: Solicitada exportação CSV para Pedido ID {pedido_id}")
        try:
            pedido_info, itens_list = models.get_pedido_details(pedido_id)
            if not pedido_info:
                messagebox.showerror("Erro", f"Pedido ID {pedido_id} não encontrado.", parent=self)
                return
            filepath = export_utils.export_to_csv(pedido_info, itens_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Pedido exportado para CSV com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_pedido_csv]: {e}")
            messagebox.showerror("Erro na Exportação CSV", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    def export_pedido_pdf(self, pedido_id: int):
        """Exporta um pedido selecionado para PDF."""
        print(f"INFO [main]: Solicitada exportação PDF para Pedido ID {pedido_id}")
        try:
            pedido_info, itens_list = models.get_pedido_details(pedido_id)
            if not pedido_info:
                messagebox.showerror("Erro", f"Pedido ID {pedido_id} não encontrado.", parent=self)
                return
            filepath = export_utils.export_to_pdf(pedido_info, itens_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Pedido exportado para PDF com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_pedido_pdf]: {e}")
            messagebox.showerror("Erro na Exportação PDF", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    # =============================================================================
    # === LÓGICA DE RELATÓRIOS ===
    # =============================================================================

    def load_relatorios_data(self, cliente_id: str = "", date_start: str = "", date_end: str = ""):
        """ Busca os dados para o Relatório no 'models' (com filtros) e atualiza a 'view'. """
        try:
            relatorios_list = models.get_report_data(cliente_id, date_start, date_end)
            self.frames["Relatorios"].refresh_data(relatorios_list)
        except Exception as e:
            print(f"ERRO [main.load_relatorios_data]: {e}")
            messagebox.showerror("Erro ao Carregar Relatório", f"Não foi possível buscar os dados do relatório:\n{e}",
                                 parent=self)

    def export_relatorio_csv(self, data_list: List[Tuple]):
        """Exporta a lista (já filtrada) da aba Relatórios para CSV."""
        print(f"INFO [main]: Solicitada exportação CSV para lista de Relatório")
        try:
            filepath = export_utils.export_list_to_csv(data_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Relatório exportado para CSV com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_relatorio_csv]: {e}")
            messagebox.showerror("Erro na Exportação CSV", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    def export_relatorio_pdf(self, data_list: List[Tuple]):
        """Exporta a lista (já filtrada) da aba Relatórios para PDF."""
        print(f"INFO [main]: Solicitada exportação PDF para lista de Relatório")
        try:
            filepath = export_utils.export_list_to_pdf(data_list)
            if filepath:
                messagebox.showinfo("Exportação Concluída", f"Relatório exportado para PDF com sucesso:\n{filepath}",
                                    parent=self)
                export_utils.open_file_externally(filepath)
        except Exception as e:
            print(f"ERRO [main.export_relatorio_pdf]: {e}")
            messagebox.showerror("Erro na Exportação PDF", f"Não foi possível exportar o arquivo:\n{e}", parent=self)

    # =============================================================================
    # === LÓGICA DE ANÁLISE IA ===
    # =============================================================================

    def start_analysis_thread(self):
        """
        Inicia a análise de IA em uma thread separada
        para não bloquear a interface principal (GUI).
        """
        print("INFO [main]: Iniciando thread de análise de IA...")

        # Passa 'daemon=True' para que a thread
        # não impeça o aplicativo de fechar.
        ia_thread = threading.Thread(target=self._run_ia_analysis, daemon=True)
        ia_thread.start()

    def _run_ia_analysis(self):
        """
        Função que roda na thread.
        Chama o 'utils' para fazer a análise (que é demorada)
        e atualiza a UI com o resultado.
        """
        try:
            # 1. Coloca a UI em modo "carregando"
            self.frames["Dashboard"].set_analysis_state(True)

            # 2. Chama a função bloqueante (utils)
            print("INFO [main._run_ia_analysis]: Chamando utils.analisar_pedidos_ia()...")
            resposta_ia = utils.analisar_pedidos_ia()

            # 3. Atualiza a UI com o resultado
            self.frames["Dashboard"].set_analysis_result(resposta_ia)

        except Exception as e:
            # Pega qualquer erro inesperado na thread
            print(f"ERRO [main._run_ia_analysis]: Falha crítica na thread de IA: {e}")
            erro_msg = f"Ocorreu um erro inesperado durante a análise:\n{e}"
            self.frames["Dashboard"].set_analysis_result(erro_msg)

        finally:
            # 4. Garante que a UI volte ao estado normal
            self.frames["Dashboard"].set_analysis_state(False)
            print("INFO [main._run_ia_analysis]: Thread de análise finalizada.")

    # =============================================================================
    # === LÓGICA DE HISTÓRICO ===
    # =============================================================================

    def load_historico_data(self):
        """ Busca o conteúdo do log no 'app_logger' e atualiza a 'view'. """
        print("INFO [main]: Carregando histórico de logs...")
        try:
            self.frames["Historico"].set_loading_state(True)
            log_content = app_logger.read_log()
            self.frames["Historico"].set_log_content(log_content)
        except Exception as e:
            print(f"ERRO [main.load_historico_data]: {e}")
            messagebox.showerror("Erro ao Carregar Histórico", f"Não foi possível ler o arquivo de log:\n{e}",
                                 parent=self)
            self.frames["Historico"].set_log_content(f"ERRO: {e}")
        finally:
            self.frames["Historico"].set_loading_state(False)

    def clear_historico_data(self):
        """ Pede confirmação e limpa o arquivo de log. """
        print("INFO [main]: Solicitação para limpar histórico.")
        if not messagebox.askyesno("Confirmar Limpeza",
                                   "Tem certeza que deseja limpar todo o histórico de ações?\n\n"
                                   "Esta ação não pode ser desfeita.",
                                   parent=self, icon="warning"):
            return
        try:
            self.frames["Historico"].set_loading_state(True)
            app_logger.clear_log()
            self.load_historico_data()  # Recarrega (mostrará "Histórico limpo")
            messagebox.showinfo("Sucesso", "Histórico de logs limpo com sucesso.", parent=self)
        except Exception as e:
            print(f"ERRO [main.clear_historico_data]: {e}")
            messagebox.showerror("Erro ao Limpar", f"Não foi possível limpar o arquivo de log:\n{e}", parent=self)
        finally:
            self.frames["Historico"].set_loading_state(False)


# =============================================================================
# === PONTO DE ENTRADA (EXECUÇÃO) ===
# =============================================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()
