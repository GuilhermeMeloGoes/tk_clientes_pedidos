import db
from typing import List, Dict, Any, Tuple
import sqlite3  # Necessário para a transação


# --- Funções de Clientes ---

def get_clientes_data(search_term: str = "") -> List[Tuple]:
    """
    Busca clientes no banco de dados.
    Se search_term for fornecido, filtra por nome ou email.
    """
    if search_term:
        query = """
                SELECT id, nome, email, telefone
                FROM clientes
                WHERE nome LIKE ? \
                   OR email LIKE ?
                ORDER BY nome \
                """
        params = (f"%{search_term}%", f"%{search_term}%")
    else:
        query = """
                SELECT id, nome, email, telefone
                FROM clientes
                ORDER BY nome \
                """
        params = ()

    return db.execute_query(query, params, fetch='all')


def get_clientes_combobox_data() -> List[Tuple]:
    """
    Retorna uma lista de tuplas (id, nome) para preencher comboboxes.
    """
    query = "SELECT id, nome FROM clientes ORDER BY nome"
    return db.execute_query(query, params=(), fetch='all')


def save_cliente(cliente_data: Dict[str, Any]) -> None:
    """
    Salva (insere ou atualiza) um cliente no banco de dados.
    Levanta exceção em caso de falha (ex: email duplicado).
    """
    if cliente_data.get("id"):
        # Atualizar
        query = """
                UPDATE clientes
                SET nome     = ?, \
                    email    = ?, \
                    telefone = ?
                WHERE id = ? \
                """
        params = (
            cliente_data["nome"],
            cliente_data["email"],
            cliente_data["telefone"],
            cliente_data["id"]
        )
    else:
        # Inserir
        query = """
                INSERT INTO clientes (nome, email, telefone)
                VALUES (?, ?, ?) \
                """
        params = (
            cliente_data["nome"],
            cliente_data["email"],
            cliente_data["telefone"]
        )

    db.execute_query(query, params)  # 'fetch' é None (padrão)


def delete_cliente(cliente_id: int) -> None:
    """
    Exclui um cliente do banco de dados.
    Levanta exceção se o cliente tiver pedidos associados.
    """
    query = "DELETE FROM clientes WHERE id = ?"
    params = (cliente_id,)
    db.execute_query(query, params)


# --- Funções de Pedidos ---

def save_pedido(pedido_data: Dict[str, Any], itens_list: List[Dict[str, Any]]) -> None:
    """
    Salva um novo pedido e seus itens de forma transacional.
    """
    conn = None
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()

        # Ativa chaves estrangeiras (novamente, por segurança na conexão)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 1. Inserir o Pedido principal
        pedido_query = """
                       INSERT INTO pedidos (cliente_id, data, total)
                       VALUES (?, ?, ?) \
                       """
        pedido_params = (
            pedido_data["cliente_id"],
            pedido_data["data"],
            pedido_data["total"]
        )

        # Como execute_query não retorna o cursor,
        # vamos usar o cursor manual para pegar o lastrowid

        cursor.execute(pedido_query, pedido_params)
        pedido_id = cursor.lastrowid

        if not pedido_id:
            raise Exception("Falha ao obter o ID do novo pedido.")

        # 2. Inserir os Itens do Pedido
        item_query = """
                     INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit)
                     VALUES (?, ?, ?, ?) \
                     """

        # Prepara os parâmetros para 'executemany'
        itens_params_list = []
        for item in itens_list:
            itens_params_list.append((
                pedido_id,
                item["produto"],
                item["quantidade"],
                item["preco_unit"]
            ))

        cursor.executemany(item_query, itens_params_list)

        # 3. Commit da Transação
        conn.commit()

    except sqlite3.Error as e:
        print(f"Erro na transação de salvar pedido: {e}")
        if conn:
            conn.rollback()  # Desfaz tudo se algo deu errado
        raise e  # Re-levanta o erro para o main.py/view

    finally:
        if conn:
            conn.close()


def get_filtered_pedidos_data(search_term: str = "",
                              date_start: str = "",
                              date_end: str = "") -> List[Tuple]:
    """
    Busca pedidos no banco de dados com filtros.
    - search_term: Filtra por nome ou email do cliente.
    - date_start/date_end: Filtra por intervalo de datas (formato YYYY-MM-DD).
    """

    params = []

    # Query base com JOIN
    query_base = """
                 SELECT p.id, p.data, c.nome, p.total
                 FROM pedidos p
                          JOIN clientes c ON p.cliente_id = c.id \
                 """

    # Lista de condições WHERE
    where_conditions = []

    # 1. Filtro de Busca (Nome/Email)
    if search_term:
        where_conditions.append("(c.nome LIKE ? OR c.email LIKE ?)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    # 2. Filtro de Data Inicial
    if date_start:
        where_conditions.append("p.data >= ?")
        params.append(date_start)

    # 3. Filtro de Data Final
    if date_end:
        where_conditions.append("p.data <= ?")
        params.append(date_end)

    # Monta a query final
    if where_conditions:
        query_final = query_base + " WHERE " + " AND ".join(where_conditions)
    else:
        query_final = query_base

    query_final += " ORDER BY p.data DESC"

    # print(f"DEBUG [get_filtered_pedidos_data] Query: {query_final}\nParams: {tuple(params)}")

    return db.execute_query(query_final, tuple(params), fetch='all')


def delete_pedido(pedido_id: int) -> None:
    """
    Exclui um pedido do banco de dados.
    (Os itens são excluídos automaticamente via 'ON DELETE CASCADE')
    """
    query = "DELETE FROM pedidos WHERE id = ?"
    params = (pedido_id,)
    db.execute_query(query, params)


def get_pedido_details(pedido_id: int) -> (Dict[str, Any], List[Dict[str, Any]]):
    """
    Busca os detalhes de um pedido (info principal) e seus itens.
    Usado para a exportação.
    """

    # 1. Buscar Informações Principais (JOIN com cliente)
    pedido_info_query = """
                        SELECT p.id, p.data, p.total, c.nome as cliente_nome
                        FROM pedidos p
                                 JOIN clientes c ON p.cliente_id = c.id
                        WHERE p.id = ? \
                        """
    pedido_info_tuple = db.execute_query(pedido_info_query, (pedido_id,), fetch='one')

    if not pedido_info_tuple:
        raise Exception(f"Pedido com ID {pedido_id} não encontrado.")

    # Converte a tupla de info para dicionário
    pedido_info_dict = {
        "id": pedido_info_tuple[0],
        "data": pedido_info_tuple[1],
        "total": pedido_info_tuple[2],
        "cliente_nome": pedido_info_tuple[3]
    }

    # 2. Buscar Itens do Pedido
    itens_query = """
                  SELECT produto, quantidade, preco_unit
                  FROM itens_pedido
                  WHERE pedido_id = ? \
                  """
    itens_list_tuples = db.execute_query(itens_query, (pedido_id,), fetch='all')

    # Converte a lista de tuplas de itens para lista de dicionários
    itens_list_dict = []
    for item_tuple in itens_list_tuples:
        itens_list_dict.append({
            "produto": item_tuple[0],
            "quantidade": item_tuple[1],
            "preco_unit": item_tuple[2]
        })

    return pedido_info_dict, itens_list_dict