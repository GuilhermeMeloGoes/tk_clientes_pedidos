import sqlite3
import logging

# --- Configuração ---
DB_FILE = "database.db"
log = logging.getLogger(__name__)


def init_db():
    """
    Inicializa o banco de dados.
    Cria as tabelas se elas não existirem.
    """
    log.info("Verificando e inicializando o banco de dados...")

    # Comandos SQL para criar as tabelas
    # (Usando 'IF NOT EXISTS' para segurança)

    create_clientes_table = """
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT,
        telefone TEXT
    );
    """

    create_pedidos_table = """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        total REAL NOT NULL,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            ON DELETE RESTRICT -- Impede excluir cliente com pedido
            ON UPDATE CASCADE
    );
    """

    create_itens_pedido_table = """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        produto TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_unit REAL NOT NULL,
        FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
            ON DELETE CASCADE -- Exclui itens se o pedido for excluído
            ON UPDATE CASCADE
    );
    """

    # (Opcional) Índices para otimizar buscas
    create_idx_cliente_nome = "CREATE INDEX IF NOT EXISTS idx_cliente_nome ON clientes(nome);"
    create_idx_pedido_cliente = "CREATE INDEX IF NOT EXISTS idx_pedido_cliente ON pedidos(cliente_id);"
    create_idx_item_pedido = "CREATE INDEX IF NOT EXISTS idx_item_pedido ON itens_pedido(pedido_id);"

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Habilita chaves estrangeiras
        cursor.execute("PRAGMA foreign_keys = ON")

        # Executa a criação das tabelas
        cursor.execute(create_clientes_table)
        cursor.execute(create_pedidos_table)
        cursor.execute(create_itens_pedido_table)

        # Executa a criação dos índices
        cursor.execute(create_idx_cliente_nome)
        cursor.execute(create_idx_pedido_cliente)
        cursor.execute(create_idx_item_pedido)

        conn.commit()
        log.info("Banco de dados pronto.")

    except sqlite3.Error as e:
        log.error(f"Erro ao inicializar o banco de dados: {e}")
        if conn:
            conn.rollback()
        raise  # Propaga o erro para o main.py
    finally:
        if conn:
            conn.close()


def execute_query(query, params=(), commit=False, fetch_all=False, fetch_one=False):
    """
    Função utilitária para executar consultas SQL no banco de dados.
    Gerencia conexão, cursor, transações e tratamento de erros.

    Args:
        query (str): A consulta SQL (com placeholders '?').
        params (tuple, optional): Os parâmetros para a consulta.
        commit (bool, optional): Define se a transação deve ser comitada (INSERT, UPDATE, DELETE).
        fetch_all (bool, optional): Define se deve retornar todos os resultados (SELECT).
        fetch_one (bool, optional): Define se deve retornar apenas um resultado (SELECT).

    Returns:
        list or tuple or None: O resultado da consulta (se fetch_all ou fetch_one) ou None.

    Raises:
        sqlite3.Error: Propaga erros do SQLite para o chamador (Model).
    """

    # Garante que fetch_all e fetch_one não sejam usados juntos
    if fetch_all and fetch_one:
        log.error("execute_query chamada com fetch_all e fetch_one.")
        raise ValueError("fetch_all e fetch_one não podem ser True simultaneamente.")

    conn = None
    result = None

    try:
        conn = sqlite3.connect(DB_FILE)
        # Habilita chaves estrangeiras para CADA conexão
        conn.execute("PRAGMA foreign_keys = ON")

        cursor = conn.cursor()
        cursor.execute(query, params)

        if commit:
            conn.commit()
            log.debug(f"Query comitada: {query[:30]}...")

        if fetch_all:
            result = cursor.fetchall()
            log.debug(f"Query (fetch_all) executada. {len(result)} linhas retornadas.")

        elif fetch_one:
            result = cursor.fetchone()
            log.debug(f"Query (fetch_one) executada. Resultado: {'Encontrado' if result else 'Nenhum'}")

        # Se nem commit, fetch_all ou fetch_one for True,
        # a query é apenas executada (útil para PRAGMA, etc.)

    except sqlite3.Error as e:
        log.error(f"Erro ao executar query: {e}\nQuery: {query}\nParams: {params}")
        if conn:
            conn.rollback()  # Desfaz em caso de erro

        # Propaga o erro (o model.py vai tratar IntegrityError, etc.)
        raise e

    finally:
        if conn:
            conn.close()

    return result


# --- Bloco de Teste ---
if __name__ == "__main__":
    """
    Executado apenas quando 'python db.py' é chamado diretamente.
    Inicializa o banco de dados.
    """
    logging.basicConfig(level=logging.INFO)
    init_db()

