Sistema de Clientes e Pedidos (Tkinter)

Este é um sistema de desktop simples para gerenciamento de clientes e pedidos, desenvolvido em Python 3 com a biblioteca nativa Tkinter e um banco de dados SQLite.

A aplicação segue uma arquitetura separada por responsabilidades (Model-View-Controller), onde:

main.py: Atua como o Controlador (Controller), conectando a lógica de negócios e a interface.

models.py: Contém a lógica de negócios e acesso ao banco de dados (Model).

views/: Contém os componentes de interface do usuário (View).

db.py: Gerencia a conexão e a criação do schema do banco de dados.

utils.py: Armazena funções de validação reutilizáveis.

Recursos

Gerenciamento de Clientes:

Listar, buscar (por nome/email), adicionar, editar e excluir clientes.

Gerenciamento de Pedidos:

Listar, buscar (por cliente/ID), adicionar, editar e excluir pedidos.

Ao criar/editar um pedido, é possível adicionar/remover itens (produto, qtd, preço).

Cálculo automático do total do pedido.

Banco de Dados:

Uso de SQLite para persistência local.

Uso de PRAGMA foreign_keys = ON para garantir integridade (um cliente com pedidos não pode ser excluído).

Salvamento de pedidos e exclusões de forma transacional (usando COMMIT e ROLLBACK).

UX (Experiência do Usuário):

Validação de formulários (campos obrigatórios, formatos de email, números).

Mensagens de confirmação para exclusão.

Prevenção de fechamento de janelas com dados não salvos.

Como Executar

Este projeto utiliza apenas bibliotecas padrão do Python (stdlib), como tkinter e sqlite3.

Pré-requisitos

Python 3.x (Tkinter já está incluído na instalação padrão do Python no Windows).

Instalação

Nenhuma instalação de dependências externas (pip) é necessária.

Execução

Clone ou baixe os arquivos do projeto para um diretório em seu computador.

O banco de dados (database.db) será criado automaticamente no mesmo diretório na primeira vez que a aplicação for executada.

Para iniciar o programa, execute o arquivo main.py:

# No Windows
python main.py

# No macOS / Linux
python3 main.py


Registro de IA

Esta seção documenta os principais prompts de interação utilizados com a IA (Gemini) durante o desenvolvimento deste projeto:

Schema e DB Inicial: "Crie, para um app Tkinter, o esquema de SQLite com tabelas clientes, pedidos e itens_pedido. Gere funções Python em db.py para inicializar o banco e executar comandos parametrizados com tratamento de erros."

Formulário de Cliente: "Gere um formulário Tkinter (janela Toplevel) para cadastrar/editar Clientes com campos nome, e-mail e telefone. Valide: nome obrigatório, e-mail em formato simples, telefone com 8–15 dígitos. Inclua botões Salvar/Cancelar e callbacks separados."

Lista de Clientes: "Crie um frame Tkinter com Treeview para listar clientes, com barra de busca por nome/email e botões Novo/Editar/Excluir. Ao excluir, peça confirmação. Recarregue a lista após operações."

Formulário de Pedido (Transacional): "Implemente uma janela Tkinter para criar Pedido: selecione Cliente (Combobox), campo Data, tabela de itens (produto/quantidade/preço), botões Adicionar/Remover item e cálculo automático do total. Salve em pedidos e itens_pedido de forma transacional."

Melhorias de UX: "Melhore UX do app: mensagens amigáveis (messagebox), validações com feedback, prevenção de fechar janela com dados não salvos, e try/except com logs simples."

Refatoração (Utils): "me traga o arquivo utils com base nesse projetos que fizemos" e "refatore minhas duas classes view uma vez que ja trouxemos diversas funções para o arquivo utils".

Criação do Controlador Principal: "agora me traga o código que vai no arquivo main".

Refatoração da View de Pedidos: "eu preciso que vc me traga o pedido_view como se fosse uma tela igual ao do cliente_view, permitindo apenas cadastrar um pedido caso exista cliente no banco de dados".

Ciclos de Depuração: O desenvolvimento incluiu vários ciclos de depuração iterativa baseados em logs de erro (Traceback) fornecidos pelo usuário. Isso permitiu corrigir TypeError (validações, argumentos de __init__), AttributeError (nomes de métodos em models.py) e sqlite3.OperationalError (lógica de transação e fetch_last_row_id em db.py), alinhando a comunicação entre todos os arquivos do projeto.