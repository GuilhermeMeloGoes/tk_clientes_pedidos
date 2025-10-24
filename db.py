import sqlite3
import logging
import os

# --- Configuração ---
DATABASE_FILE = "database.db"
log = logging.getLogger(__name__)

# --- Conexão Singleton (para garantir uma única conexão) ---
_connection = None


def get_db_connection():
    """Retorna a conexão singleton com o banco de dados."""
    global _connection
    if _connection is None:
        try:
            # Usamos o isolation_level padrão (DEFERRED) para que as
            # transações sejam gerenciadas manualmente (com COMMIT/ROLLBACK).
            _connection = sqlite3.connect(DATABASE_FILE)
            # Ativa o suporte a Foreign Keys (desativado por padrão no SQLite)
            _connection.execute("PRAGMA foreign_keys = ON;")
            log.info(f"Conexão com o banco de dados '{DATABASE_FILE}' estabelecida.")
        except sqlite3.Error as e:
            log.critical(f"Falha ao conectar ao banco de dados: {e}", exc_info=True)
            raise
    return _connection


def close_db_connection():
    """Fecha a conexão com o banco de dados, se estiver aberta."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        log.info("Conexão com o banco de dados fechada.")


# --- Inicialização ---

def init_db():
    """
    Cria as tabelas do banco de dados se elas não existirem.
    """
    log.info("Verificando e inicializando o banco de dados...")

    # Comandos SQL para criar tabelas (schema)
    # Usamos 'IF NOT EXISTS' para segurança

    create_clientes_table = """
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL CHECK(length(nome) > 0),
        email TEXT UNIQUE,
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
    );
    """

    create_itens_pedido_table = """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        produto TEXT NOT NULL CHECK(length(produto) > 0),
        quantidade INTEGER NOT NULL CHECK(quantidade > 0),
        preco_unit REAL NOT NULL CHECK(preco_unit >= 0),
        FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
            ON DELETE CASCADE -- Exclui itens se o pedido for excluído
    );
    """

    try:
        # Executa os comandos de criação
        # Usamos execute_query para garantir que a conexão única seja usada
        execute_query(create_clientes_table, commit=True)
        execute_query(create_pedidos_table, commit=True)
        execute_query(create_itens_pedido_table, commit=True)

        log.info("Banco de dados pronto.")

    except Exception as e:
        log.error(f"Falha ao inicializar o banco de dados: {e}", exc_info=True)
        raise


# --- Função de Execução Genérica ---

def execute_query(query, params=(), commit=False, fetch_all=False, fetch_one=False, fetch_last_row_id=False):
    """
    Executa um comando SQL genérico no banco de dados.

    Parâmetros:
        query (str): O comando SQL a ser executado.
        params (tuple): Parâmetros para a query (para evitar SQL Injection).
        commit (bool): Se True, executa con.commit() (para INSERT, UPDATE, DELETE).
        fetch_all (bool): Se True, retorna todos os resultados (para SELECT).
        fetch_one (bool): Se True, retorna o primeiro resultado (para SELECT).
        fetch_last_row_id (bool): Se True, retorna o ID da última linha inserida.
    """
    con = None
    try:
        con = get_db_connection()  # Obtém a conexão singleton
        cursor = con.cursor()

        log.debug(f"Executando Query: {query} com Params: {params}")
        cursor.execute(query, params)

        result = None
        query_upper = query.strip().upper()

        # Lógica de Transação Manual (para models.py)
        if query_upper.startswith("COMMIT"):
            con.commit()
            log.debug("Transação comitada (COMMIT).")
        elif query_upper.startswith("ROLLBACK"):
            con.rollback()
            log.debug("Transação revertida (ROLLBACK).")

        # Lógica de Autocommit (para queries simples)
        elif commit:
            con.commit()
            log.debug("Query comitada (commit=True).")

        # Lógica de Retorno de Dados (só pode ser um)
        if fetch_last_row_id:
            result = cursor.lastrowid
            log.debug(f"Query retornou lastrowid: {result}")
        elif fetch_all:
            result = cursor.fetchall()
            log.debug(f"Query retornou fetch_all (count: {len(result) if result else 0}).")
        elif fetch_one:
            result = cursor.fetchone()
            log.debug(f"Query retornou fetch_one (Result: {'None' if not result else 'OK'}).")

        return result

    except sqlite3.Error as e:
        log.error(f"Erro no SQLite ao executar query: {query} | Erro: {e}", exc_info=True)

        # Tenta reverter se houver uma transação ativa
        if con and con.in_transaction:
            # Evita tentar reverter se a própria query de rollback falhar
            if not query_upper.startswith("ROLLBACK"):
                try:
                    con.rollback()
                    log.warning("Erro detectado, transação revertida (ROLLBACK).")
                except sqlite3.Error as re:
                    log.critical(f"Falha ao reverter (ROLLBACK) transação após erro: {re}", exc_info=True)

        raise e  # Levanta a exceção original para o model/controller


# --- Bloco de Teste ---
if __name__ == "__main__":
    """
    Se este arquivo for executado diretamente,
    ele apenas inicializa o banco de dados.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    log.info("Executando db.py diretamente: Inicializando o banco de dados...")

    try:
        init_db()
        log.info("Banco de dados inicializado com sucesso.")

        # Teste de inserção e busca (opcional)
        log.info("Testando inserção de cliente (se não existir)...")
        # 'OR IGNORE' ignora o erro se o email (UNIQUE) já existir
        execute_query(
            "INSERT OR IGNORE INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
            ("Cliente Teste", "teste@db.com", "123456"),
            commit=True
        )

        log.info("Testando busca de cliente...")
        cliente = execute_query("SELECT * FROM clientes WHERE email = ?", ("teste@db.com",), fetch_one=True)
        if cliente:
            log.info(f"Cliente de teste encontrado: {cliente}")
        else:
            log.error("Cliente de teste não encontrado.")

    except Exception as e:
        log.critical(f"Falha na execução de db.py: {e}", exc_info=True)
    finally:
        close_db_connection()

