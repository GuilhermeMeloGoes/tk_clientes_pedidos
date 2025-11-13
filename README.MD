Projeto Tkinter - Sistema de Gerenciamento (Tkinter, SQLite, IA)

Este é um aplicativo de desktop completo para gerenciamento de clientes e pedidos, desenvolvido em Python 3 com a biblioteca nativa Tkinter e um banco de dados SQLite.

Recursos Principais

O sistema é composto por 5 módulos principais (telas) e diversas funcionalidades avançadas:

Dashboard: Tela inicial que exibe estatísticas vitais (Total de Clientes, Pedidos no Mês, Receita no Mês, Ticket Médio).

Clientes: Gerenciamento CRUD (Criar, Ler, Atualizar, Excluir) completo para clientes, com busca em tempo real.

Pedidos: Tela de listagem de pedidos com filtros por nome, e-mail e intervalo de datas.

Relatórios: Geração de relatórios avançados com filtros por cliente e data, exibindo pedidos e seus itens de forma consolidada.

Histórico: Um log de auditoria que registra todas as ações de criação, edição e exclusão no sistema.

Formulários (Popups): Janelas modais para "Novo Cliente", "Editar Cliente" e "Novo Pedido", com validação de dados e rastreamento de "alterações não salvas" (dirty checking).

Exportação: Capacidade de exportar pedidos únicos ou listas de relatórios inteiras para CSV e PDF (usando reportlab).

Análise de IA (Ollama): Uma funcionalidade no Dashboard que envia os dados dos últimos 5 pedidos para uma IA local (Ollama, modelo phi3) e exibe insights (ex: produtos mais vendidos, ticket médio) na interface.

UX Avançada:

Menu principal de navegação (em vez de abas).

Alternador de Tema (Claro/Escuro) funcional.

Proteção ao fechar o app se houver formulários com dados não salvos.

Como Instalar e Executar (Para Usuários Finais)

Esta seção é para usuários que receberam o arquivo executável (.exe) e não são desenvolvedores (ou seja, não possuem Python instalado).

Opção 1: Se você recebeu um arquivo .zip (Recomendado)

Esta é a versão "pasta" (criada com pyinstaller --onedir).

Descompacte o Arquivo: Clique com o botão direito no arquivo .zip (ex: SistemaDeGestao.zip) e selecione "Extrair Tudo..." (ou "Unzip").

Abra a Pasta: Entre na pasta que foi criada (ex: SistemaDeGestao).

Execute o Programa: Dê um clique duplo no arquivo .exe (ex: SistemaDeGestao.exe) para iniciar o aplicativo.

Nota: Não mova o .exe para fora desta pasta. Ele precisa dos outros arquivos que vieram juntos no .zip para funcionar.

Opção 2: Se você recebeu um único arquivo .exe

Esta é a versão "arquivo único" (criada com pyinstaller --onefile).

Execute o Programa: Apenas dê um clique duplo no arquivo .exe (ex: SistemaDeGestao.exe) para iniciar.

Nota: O primeiro início pode ser um pouco mais lento, pois o programa precisa se descompactar temporariamente.

Aviso Importante: Análise de IA (Ollama)

A funcionalidade "Analisar Pedidos (IA)" não funcionará para o usuário final, a menos que ele (separadamente) instale e configure o Ollama em sua própria máquina.

O aplicativo mostrará um erro de conexão se o Ollama não estiver rodando localmente em http://localhost:11434.

Todas as outras funcionalidades (Clientes, Pedidos, Relatórios, PDF, etc.) funcionarão perfeitamente sem o Ollama.

Como Executar (para Desenvolvedores)

Esta seção é para desenvolvedores que desejam executar o código-fonte Python (.py).

1. Pré-requisitos (Dev)

Python 3.10 ou mais recente.

(Opcional) Ollama instalado e rodando para a funcionalidade de IA.

2. Instalação (Dev)

Clone ou Baixe o Projeto:
Obtenha todos os arquivos (.py, README.MD, requirements.txt) e coloque-os em uma pasta.

Crie um Ambiente Virtual (Recomendado):

python -m venv .venv


Ative o Ambiente Virtual:

No Windows (PowerShell): .\.venv\Scripts\Activate.ps1

No Windows (CMD): .\.venv\Scripts\activate.bat

No macOS/Linux: source .venv/bin/activate

Instale as Dependências:
O projeto usa algumas bibliotecas externas. Instale-as usando o requirements.txt:

pip install -r requirements.txt


3. (Opcional) Configurando a Análise de IA (Dev)

Instale o Ollama: Baixe e instale em ollama.com.

Execute o Ollama: Inicie o aplicativo Ollama (ele ficará rodando em segundo plano).

Baixe o Modelo (phi3): Abra seu terminal e execute:

ollama pull phi3


4. Execute o Aplicativo (Dev)

Com o ambiente ativado e as dependências instaladas, execute o main.py:

python main.py


O banco de dados (app_database.db) e a pasta de logs (logs/) serão criados automaticamente na primeira execução.

Como Gerar o Executável (PyInstaller)

Instale o PyInstaller no seu ambiente virtual: pip install pyinstaller

Use o comando (--onedir é recomendado para depuração):

pyinstaller --name "SistemaDeGestao" --windowed --onedir --hidden-import="tkcalendar" --hidden-import="babel.numbers" --hidden-import="reportlab" main.py


Ou, para um único arquivo (.exe):

pyinstaller --name "SistemaDeGestao" --windowed --onefile --hidden-import="tkcalendar" --hidden-import="babel.numbers" --hidden-import="reportlab" main.py


O resultado estará na pasta dist/.

Arquitetura e Lógica

O projeto é dividido em módulos, cada um com uma responsabilidade clara:

main.py (O Controlador)
Este é o cérebro do aplicativo. Ele não contém nenhuma tela (View) ou lógica de SQL (Model). Sua única função é atuar como o "controlador" (Controller):

Inicializa a janela principal (App) e o Menu.

Gerencia qual tela (Frame) está visível (show_frame).

Conecta os botões das Views (ex: on_new_callback) com as funções de lógica (models.py).

Gerencia o estado global (tema claro/escuro, is_form_dirty).

Inicia threads para tarefas demoradas (como a Análise de IA) para não travar a UI.

db.py (Acesso ao Banco)
Este é o módulo de nível mais baixo. Ele não sabe o que é um "cliente" ou "pedido". Ele apenas sabe como executar SQL.

init_db(): Cria o schema do banco de dados (.db) se ele não existir.

get_db_connection(): Fornece uma conexão para o models.py (usado para transações).

execute_query(): A função principal. Executa qualquer string SQL com parâmetros, gerenciando a conexão, o cursor e o commit/rollback.

models.py (Lógica de Dados)
Este é o "Modelo" (Model). É o único arquivo que tem permissão para importar e usar o db.py.

Define as funções que o main.py chama (ex: get_clientes_data, save_pedido).

É responsável por escrever as consultas SQL.

Converte os dados brutos do banco (tuplas) em formatos úteis (dicionários, listas) quando necessário (ex: get_pedido_details).

Gerencia a lógica de transações (ex: save_pedido usa conn.commit() e conn.rollback()).

views/ (As Telas)
Esta pasta contém os arquivos da "Camada Visual" (View).

"Burros": Esses arquivos são intencionalmente "burros". Eles não sabem como salvar no banco de dados ou como a IA funciona.

Definição da UI: Eles definem os botões, labels, e Treeviews (create_widgets).

Callbacks: Eles recebem funções (callbacks) do main.py em seus construtores (__init__). Quando um botão é clicado (ex: _on_save_click), ele apenas chama o callback (ex: self.on_save(dados)).

ClienteForm / PedidoForm: São classes Toplevel (popups) que gerenciam seu próprio estado (validação, is_dirty).

utils.py (Caixa de Ferramentas)
Contém lógica auxiliar complexa ou genérica.

center_window(): Centraliza popups.

setup_light_theme() / setup_dark_theme(): Contém toda a lógica de ttk.Style para a troca de temas.

analisar_pedidos_ia(): Contém a lógica de negócios da IA. Ele busca os dados (usando o models), formata o prompt e chama a API (usando httpx e asyncio).

app_logger.py (O Auditor)
Gerencia o logs/app.log.

log_action(): Usado pelo main.py para registrar eventos (ex: "Cliente criado").

read_log() / clear_log(): Usado pela tela de "Histórico".

export_utils.py (O Exportador)
Contém a lógica de geração de arquivos.

export_to_csv() / export_to_pdf(): Usam csv e reportlab para criar os arquivos.

open_file_externally(): Usa webbrowser para abrir o arquivo gerado no programa padrão do SO.

Prompt da IA (Análise de Pedidos)

Abaixo está o prompt usado para enviar os dados dos últimos pedidos para a IA (Ollama) para análise:

Com base nos dados dos últimos 5 pedidos fornecidos abaixo, atue como um assistente de negócios e forneça um breve resumo (em 3 ou 4 pontos) sobre os insights mais importantes.

Concentre-se em:
- Quais produtos parecem ser os mais populares?
- Qual é o ticket médio (valor médio por pedido) desses pedidos?
- Há algum padrão óbvio (ex: clientes recorrentes, itens comprados juntos)?

Seja breve e direto ao ponto.

--- DADOS DOS PEDIDOS ---

{dados_formatados_aqui}
