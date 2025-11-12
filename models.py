"""
Models.py (Camada de Lógica de Dados)

Este arquivo é responsável por toda a interação com o banco de dados.
Ele contém as funções que o `main.py` (controlador) chama.
Ele usa o `db.py` (camada de acesso) para executar o SQL.
"""

import db
from typing import List, Dict, Any, Optional, Tuple


# --- Funções de Clientes ---

def get_clientes_data(search_term: str = "") -> List[Tuple]:
    """
    Busca clientes do banco de dados, com filtro opcional por nome ou email.
    Retorna uma lista de tuplas.
    """
    query = "SELECT id, nome, email, telefone FROM clientes"
    params = []

    if search_term:
        query += " WHERE nome LIKE ? OR email LIKE ?"
        params = [f"%{search_term}%", f"%{search_term}%"]

    query += " ORDER BY nome"

    return db.execute_query(query, tuple(params), fetch="all")


def save_cliente(cliente_data: Dict[str, Any]) -> None:
    """Salva um cliente (novo ou existente) no banco de dados."""
    cliente_id = cliente_data.get('id')

    if cliente_id:
        # Atualizar cliente existente
        query = "UPDATE clientes SET nome = ?, email = ?, telefone = ? WHERE id = ?"
        params = (cliente_data['nome'], cliente_data['email'], cliente_data['telefone'], cliente_id)
    else:
        # Inserir novo cliente
        query = "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)"
        params = (cliente_data['nome'], cliente_data['email'], cliente_data['telefone'])

    db.execute_query(query, params)


def delete_cliente(cliente_id: int) -> None:
    """Exclui um cliente do banco de dados."""
    query = "DELETE FROM clientes WHERE id = ?"
    params = (cliente_id,)
    db.execute_query(query, params)


def get_clientes_combobox_data() -> List[Tuple]:
    """
    Busca clientes no formato (id, nome) para os comboboxes.
    Retorna uma lista de tuplas.
    """
    query = "SELECT id, nome FROM clientes ORDER BY nome"
    return db.execute_query(query, fetch="all")


# --- Funções de Pedidos ---

def save_pedido(pedido_data: Dict[str, Any], itens_data: List[Dict[str, Any]]) -> None:
    """
    Salva um novo pedido e seus itens usando uma transação.
    Se qualquer item falhar, o pedido inteiro é revertido (rollback).
    """
    conn = None
    try:
        conn = db.get_db_connection()

        # 1. Inserir o Pedido principal
        query_pedido = "INSERT INTO pedidos (cliente_id, data, total) VALUES (?, ?, ?)"
        params_pedido = (pedido_data['cliente_id'], pedido_data['data'], pedido_data['total'])

        # Passa a conexão (conn) e espera o ID de volta
        resultado_pedido = db.execute_query(query_pedido, params_pedido, conn=conn, fetch="lastrowid")
        pedido_id = resultado_pedido

        if not pedido_id:
            raise Exception("Não foi possível obter o ID do novo pedido.")

        # 2. Inserir os Itens do Pedido
        query_item = "INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit) VALUES (?, ?, ?, ?)"

        for item in itens_data:
            params_item = (
                pedido_id,
                item['produto'],
                item['quantidade'],
                item['preco_unit']
            )
            # Passa a mesma conexão (conn)
            db.execute_query(query_item, params_item, conn=conn)

        # 3. Se tudo deu certo, commita a transação
        conn.commit()
        print(f"INFO [models.save_pedido]: Pedido {pedido_id} salvo com sucesso.")

    except Exception as e:
        print(f"ERRO [models.save_pedido]: Falha na transação. {e}")
        if conn:
            conn.rollback()  # Desfaz todas as mudanças
        # Re-levanta o erro para que o 'main.py' e a 'view' saibam que falhou
        raise e
    finally:
        if conn:
            conn.close()


def get_filtered_pedidos_data(
        search_term: str = "",
        date_start: Optional[str] = None,
        date_end: Optional[str] = None
) -> List[Tuple]:
    """
    Busca pedidos com base em filtros de cliente, data de início e data de fim.
    Usa JOIN para trazer o nome do cliente.
    Retorna uma lista de tuplas.
    """

    # Base da consulta
    query = """
            SELECT p.id,
                   p.data,
                   c.nome AS cliente_nome,
                   p.total
            FROM pedidos p
                     JOIN clientes c ON p.cliente_id = c.id
            WHERE 1 = 1 \
            """

    params = []

    # Adiciona filtros dinamicamente
    if search_term:
        query += " AND (c.nome LIKE ? OR c.email LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if date_start:
        query += " AND p.data >= ?"
        params.append(date_start)

    if date_end:
        query += " AND p.data <= ?"
        params.append(date_end)

    query += " ORDER BY p.data DESC"

    return db.execute_query(query, tuple(params), fetch="all")


def delete_pedido(pedido_id: int) -> None:
    """
    Exclui um pedido.
    Graças ao 'ON DELETE CASCADE' no db.py, os itens_pedido
    associados serão excluídos automaticamente pelo SQLite.
    """
    query = "DELETE FROM pedidos WHERE id = ?"
    params = (pedido_id,)
    db.execute_query(query, params)


def get_pedido_details(pedido_id: int) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Busca os detalhes de um pedido (para exportação).
    Retorna uma tupla: (dados_do_pedido_dict, lista_de_itens_dicts)

    CORRIGIDO: Converte as tuplas do DB em Dicionários
    """

    # 1. Buscar dados do pedido e cliente
    query_pedido = """
                   SELECT p.id, p.data, p.total, c.nome AS cliente_nome, c.email, c.telefone
                   FROM pedidos p
                            JOIN clientes c ON p.cliente_id = c.id
                   WHERE p.id = ? \
                   """
    params_pedido = (pedido_id,)
    # Usamos fetch="one" para pegar apenas uma tupla (ou None)
    pedido_tuple = db.execute_query(query_pedido, params_pedido, fetch="one")

    pedido_data = None
    if pedido_tuple:
        # Converte a tupla em dicionário
        pedido_data = {
            "id": pedido_tuple[0],
            "data": pedido_tuple[1],
            "total": pedido_tuple[2],
            "cliente_nome": pedido_tuple[3],
            "email": pedido_tuple[4],
            "telefone": pedido_tuple[5]
        }

    # 2. Buscar itens do pedido
    query_itens = """
                  SELECT produto, quantidade, preco_unit
                  FROM itens_pedido
                  WHERE pedido_id = ?
                  ORDER BY id \
                  """
    params_itens = (pedido_id,)
    # Usamos fetch="all" para pegar uma lista de tuplas
    itens_tuples = db.execute_query(query_itens, params_itens, fetch="all")

    itens_data = []
    if itens_tuples:
        # Converte a lista de tuplas em uma lista de dicionários
        for item in itens_tuples:
            itens_data.append({
                "produto": item[0],
                "quantidade": item[1],
                "preco_unit": item[2]
            })

    return pedido_data, itens_data


# --- Funções do Dashboard ---

def get_dashboard_stats() -> Dict[str, Any]:
    """
    Busca estatísticas agregadas para o Dashboard em uma única consulta.
    Retorna um dicionário.
    """

    query = """
            SELECT
                -- 1. Total de Clientes (sub-consulta)
                (SELECT COUNT(*) FROM clientes) AS total_clientes,

                -- 2. Total de Pedidos no mês atual
                COUNT(CASE
                          WHEN strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
                              THEN 1
                    END)                        AS pedidos_mes_atual,

                -- 3. Receita Total no mês atual
                SUM(CASE
                        WHEN strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
                            THEN total
                        ELSE 0
                    END)                        AS receita_total_mes

            FROM pedidos; \
            """

    stats_tuple = db.execute_query(query, fetch="one")

    # Processamento dos dados (cálculo do Ticket Médio)
    if stats_tuple:
        total_clientes = stats_tuple[0]
        pedidos_mes_atual = stats_tuple[1]
        receita_total_mes = stats_tuple[2] if stats_tuple[2] is not None else 0.0

        # Calcula o ticket médio
        ticket_medio = 0.0
        if pedidos_mes_atual > 0:
            ticket_medio = receita_total_mes / pedidos_mes_atual

        return {
            "total_clientes": total_clientes,
            "pedidos_mes_atual": pedidos_mes_atual,
            "receita_total_mes": receita_total_mes,
            "ticket_medio_mes_atual": ticket_medio
        }
    else:
        # Caso de emergência (ex: banco de dados vazio)
        return {
            "total_clientes": 0,
            "pedidos_mes_atual": 0,
            "receita_total_mes": 0.0,
            "ticket_medio_mes_atual": 0.0
        }


# --- Funções de Relatórios ---

def get_report_data(
        cliente_id: str = "",
        date_start: Optional[str] = None,
        date_end: Optional[str] = None
) -> List[Tuple]:
    """
    Busca dados agregados para o Relatório, agrupando itens por pedido.
    Usa GROUP_CONCAT para juntar os itens em uma string.
    """

    # Base da consulta com Sub-query para os itens
    query = """
            SELECT p.id,
                   p.data,
                   c.nome                      AS cliente_nome,
                   (SELECT GROUP_CONCAT(ip.produto || ' (' || ip.quantidade || ')', ', ')
                    FROM itens_pedido ip
                    WHERE ip.pedido_id = p.id) AS itens_str,
                   p.total
            FROM pedidos p
                     JOIN clientes c ON p.cliente_id = c.id
            WHERE 1 = 1 \
            """

    params = []

    # Adiciona filtros dinamicamente
    if cliente_id:
        query += " AND p.cliente_id = ?"
        params.append(cliente_id)

    if date_start:
        query += " AND p.data >= ?"
        params.append(date_start)

    if date_end:
        query += " AND p.data <= ?"
        params.append(date_end)

    query += " ORDER BY p.data DESC, c.nome"

    return db.execute_query(query, tuple(params), fetch="all")


# --- Funções de Análise IA (NOVO) ---

def get_last_n_order_ids(n: int = 5) -> List[int]:
    """
    Busca os IDs dos N últimos pedidos (os mais recentes).
    Retorna uma lista de IDs.
    """
    query = """
            SELECT id
            FROM pedidos
            ORDER BY data DESC, id DESC LIMIT ? \
            """
    params = (n,)

    # Retorna uma lista de tuplas, ex: [(10,), (9,), (8,)]
    results_tuples = db.execute_query(query, params, fetch="all")

    # Converte em uma lista de ints: [10, 9, 8]
    ids = [row[0] for row in results_tuples]
    return ids
