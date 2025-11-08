import sqlite3
from typing import Any, List, Tuple, Optional

# Nome do arquivo do banco de dados
DB_NAME = "app_database.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Cria e retorna uma nova conexão com o banco de dados.
    Configurada para retornar dicionários (Row factory).
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        # Retorna linhas que funcionam como dicionários
        # conn.row_factory = sqlite3.Row

        # Vamos manter como tuplas por enquanto, pois
        # as views (refresh_data) já esperam tuplas.
        # Se mudarmos para 'Row', teríamos que
        # converter em 'dict' ou acessar por índice.

        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise e


def init_db():
    """
    Cria as tabelas do banco de dados se elas não existirem.
    """
    # Definição das tabelas
    # CORRIGIDO: Trocado 'NOT JOIN' por 'NOT NULL'
    CREATE_CLIENTES_TABLE = """
                            CREATE TABLE IF NOT EXISTS clientes \
                            ( \
                                id \
                                INTEGER \
                                PRIMARY \
                                KEY \
                                AUTOINCREMENT, \
                                nome \
                                TEXT \
                                NOT \
                                NULL, \
                                email \
                                TEXT \
                                UNIQUE, \
                                telefone \
                                TEXT
                            ); \
                            """

    # CORRIGIDO: Trocado 'NOT AT' por 'NOT NULL'
    CREATE_PEDIDOS_TABLE = """
                           CREATE TABLE IF NOT EXISTS pedidos \
                           ( \
                               id \
                               INTEGER \
                               PRIMARY \
                               KEY \
                               AUTOINCREMENT, \
                               cliente_id \
                               INTEGER \
                               NOT \
                               NULL, \
                               data \
                               TEXT \
                               NOT \
                               NULL, \
                               total \
                               REAL \
                               NOT \
                               NULL, \
                               FOREIGN \
                               KEY \
                           ( \
                               cliente_id \
                           ) REFERENCES clientes \
                           ( \
                               id \
                           )
                               ); \
                           """

    CREATE_ITENS_PEDIDO_TABLE = """
                                CREATE TABLE IF NOT EXISTS itens_pedido \
                                ( \
                                    id \
                                    INTEGER \
                                    PRIMARY \
                                    KEY \
                                    AUTOINCREMENT, \
                                    pedido_id \
                                    INTEGER \
                                    NOT \
                                    NULL, \
                                    produto \
                                    TEXT \
                                    NOT \
                                    NULL, \
                                    quantidade \
                                    INTEGER \
                                    NOT \
                                    NULL, \
                                    preco_unit \
                                    REAL \
                                    NOT \
                                    NULL, \
                                    FOREIGN \
                                    KEY \
                                ( \
                                    pedido_id \
                                ) REFERENCES pedidos \
                                ( \
                                    id \
                                ) ON DELETE CASCADE
                                    ); \
                                """

    PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON;"

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ativa a checagem de chave estrangeira
        cursor.execute(PRAGMA_FOREIGN_KEYS)

        # Cria as tabelas
        cursor.execute(CREATE_CLIENTES_TABLE)
        cursor.execute(CREATE_PEDIDOS_TABLE)
        cursor.execute(CREATE_ITENS_PEDIDO_TABLE)

        conn.commit()

    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
        if conn:
            conn.rollback()
        raise e  # Re-levanta o erro para o main.py

    finally:
        if conn:
            conn.close()


def execute_query(query: str,
                  params: tuple = (),
                  conn: Optional[sqlite3.Connection] = None,
                  fetch: Optional[str] = None) -> Any:
    """
    Executa uma consulta SQL genérica no banco de dados.

    :param query: A string da consulta SQL.
    :param params: Uma tupla de parâmetros para a consulta.
    :param conn: (Opcional) Uma conexão existente (para transações).
                 Se None, uma nova conexão será criada e fechada.
    :param fetch: (Opcional) Tipo de fetch:
                  'all' -> fetchall()
                  'one' -> fetchone()
                  'lastrowid' -> cursor.lastrowid
                  None (default) -> Apenas executa (INSERT, UPDATE, DELETE)
    :return: O resultado da consulta (se houver) ou None.
    :raises: sqlite3.Error em caso de falha.
    """

    # Gerencia a conexão: usa a externa (transação) ou cria uma nova.
    is_external_conn = conn is not None
    if not is_external_conn:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Ativa chaves estrangeiras para CADA conexão (necessário no SQLite)
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute(query, params)

        result = None
        if fetch == 'all':
            result = cursor.fetchall()  # Retorna List[Tuple]
        elif fetch == 'one':
            result = cursor.fetchone()  # Retorna Tuple
        elif fetch == 'lastrowid':
            result = cursor.lastrowid  # Retorna int (ID)

        # Se a conexão for interna, commitamos.
        # Se for externa, o 'models.py' (transação) é quem comita.
        if not is_external_conn:
            conn.commit()

        return result

    except sqlite3.Error as e:
        print(f"Erro ao executar a consulta: {e}\nConsulta: {query}\nParâmetros: {params}")
        if not is_external_conn:
            # Só faz rollback se for uma conexão interna que falhou
            conn.rollback()
        raise e  # Re-levanta a exceção para a camada de modelo/controller

    finally:
        # Só fecha a conexão se ela foi criada internamente
        if not is_external_conn and conn:
            conn.close()