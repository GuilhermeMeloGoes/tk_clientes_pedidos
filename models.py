import logging
from db import execute_query  # Importa a função centralizada de query

log = logging.getLogger(__name__)


class ClienteModel:
    """
    Classe Model para gerenciar a lógica de negócios e
    interações com o banco de dados para Clientes.
    """

    def __init__(self):
        log.info("ClienteModel instanciado.")

    def find_clients(self, search_term=""):
        """
        Busca clientes no banco de dados por nome ou email.
        Se search_term estiver vazio, retorna todos os clientes.
        """
        try:
            if search_term:
                query = "SELECT id, nome, email, telefone FROM clientes WHERE nome LIKE ? OR email LIKE ? "
                # O termo de busca deve ser formatado para o LIKE
                term = f"%{search_term}%"
                params = (term, term)
            else:
                query = "SELECT id, nome, email, telefone FROM clientes"
                params = ()

            # Usa fetch_all=True para obter todos os resultados
            return execute_query(query, params, fetch_all=True)

        except Exception as e:
            log.error(f"Erro em find_clients: {e}", exc_info=True)
            # Levanta a exceção para ser tratada pelo controlador (main.py)
            raise

    def get_client_by_id(self, cliente_id):
        """Busca um cliente específico pelo ID e retorna como um dicionário."""
        try:
            query = "SELECT id, nome, email, telefone FROM clientes WHERE id = ?"
            # Usa fetch_one=True
            result = execute_query(query, (cliente_id,), fetch_one=True)

            if result:
                # Converte a tupla (id, nome, email, tel) em um dicionário
                return {'id': result[0], 'nome': result[1], 'email': result[2], 'telefone': result[3]}
            return None

        except Exception as e:
            log.error(f"Erro em get_client_by_id (ID: {cliente_id}): {e}", exc_info=True)
            raise

    def add_client(self, nome, email, telefone):
        """Adiciona um novo cliente ao banco de dados."""
        try:
            query = "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)"
            # Usa commit=True para salvar a alteração
            execute_query(query, (nome, email, telefone), commit=True)
            log.info(f"Cliente '{nome}' adicionado com sucesso.")
            return {"success": True}
        except Exception as e:
            log.error(f"Erro ao adicionar cliente '{nome}': {e}", exc_info=True)
            raise

    def update_client(self, cliente_id, nome, email, telefone):
        """Atualiza os dados de um cliente existente."""
        try:
            query = "UPDATE clientes SET nome = ?, email = ?, telefone = ? WHERE id = ?"
            # Usa commit=True
            execute_query(query, (nome, email, telefone, cliente_id), commit=True)
            log.info(f"Cliente ID {cliente_id} atualizado com sucesso.")
            return {"success": True}
        except Exception as e:
            log.error(f"Erro ao atualizar cliente ID {cliente_id}: {e}", exc_info=True)
            raise

    def delete_client(self, cliente_id):
        """Exclui um cliente do banco de dados."""
        try:
            # 1. Verifica se o cliente tem pedidos associados
            check_query = "SELECT 1 FROM pedidos WHERE cliente_id = ?"
            has_pedidos = execute_query(check_query, (cliente_id,), fetch_one=True)

            if has_pedidos:
                msg = f"Não é possível excluir o cliente ID {cliente_id}, pois ele possui pedidos cadastrados."
                log.warning(msg)
                return {"success": False, "message": msg}

            # 2. Se não tiver, exclui o cliente
            query = "DELETE FROM clientes WHERE id = ?"
            # Usa commit=True
            execute_query(query, (cliente_id,), commit=True)
            log.info(f"Cliente ID {cliente_id} excluído com sucesso.")
            return {"success": True}

        except Exception as e:
            # Trata erros de integridade (como FK, caso o check falhe)
            if "FOREIGN KEY constraint failed" in str(e):
                msg = f"Não é possível excluir o cliente ID {cliente_id} (Constraint Error), pois ele possui pedidos."
                log.warning(msg)
                return {"success": False, "message": msg}

            log.error(f"Erro ao excluir cliente ID {cliente_id}: {e}", exc_info=True)
            raise

    def get_all_clients_list(self):
        """Retorna uma lista de tuplas (id, nome) de todos os clientes."""
        try:
            query = "SELECT id, nome FROM clientes"
            return execute_query(query, fetch_all=True)
        except Exception as e:
            log.error(f"Erro ao buscar lista simples de clientes: {e}", exc_info=True)
            raise


class PedidoModel:
    """
    Classe Model para gerenciar a lógica de negócios e
    interações com o banco de dados para Pedidos.
    """

    def __init__(self):
        log.info("PedidoModel instanciado.")

    def find_pedidos(self, search_term=""):
        """
        Busca pedidos no banco de dados, juntando o nome do cliente.
        Se search_term estiver vazio, retorna todos os pedidos.
        """
        try:
            # Query base que junta pedidos e clientes
            base_query = """
                SELECT p.id, c.nome, p.data, p.total 
                FROM pedidos p
                JOIN clientes c ON p.cliente_id = c.id
            """

            if search_term:
                # Busca pelo nome do cliente ou ID do pedido
                query = base_query + " WHERE c.nome LIKE ? OR p.id LIKE ?"
                term = f"%{search_term}%"
                params = (term, term)
            else:
                query = base_query
                params = ()

            # Usa fetch_all=True
            return execute_query(query, params, fetch_all=True)

        except Exception as e:
            log.error(f"Erro em find_pedidos: {e}", exc_info=True)
            raise

    def get_pedido_details(self, pedido_id):
        """
        Busca os detalhes completos de um pedido (info + itens) pelo ID.
        Retorna um dicionário estruturado.
        """
        try:
            # 1. Busca informações principais do pedido
            query_pedido = "SELECT id, cliente_id, data, total FROM pedidos WHERE id = ?"
            pedido_info_tuple = execute_query(query_pedido, (pedido_id,), fetch_one=True)

            if not pedido_info_tuple:
                return None  # Pedido não encontrado

            pedido_info = {
                'id': pedido_info_tuple[0],
                'cliente_id': pedido_info_tuple[1],
                'data': pedido_info_tuple[2],
                'total': pedido_info_tuple[3]
            }

            # 2. Busca os itens do pedido
            query_itens = "SELECT produto, quantidade, preco_unit FROM itens_pedido WHERE pedido_id = ?"
            itens_tuple_list = execute_query(query_itens, (pedido_id,), fetch_all=True)

            itens_list = []
            for item_tuple in itens_tuple_list:
                itens_list.append({
                    'produto': item_tuple[0],
                    'quantidade': item_tuple[1],
                    'preco_unit': item_tuple[2]
                })

            # 3. Retorna o dicionário combinado
            return {'pedido_info': pedido_info, 'itens': itens_list}

        except Exception as e:
            log.error(f"Erro em get_pedido_details (ID: {pedido_id}): {e}", exc_info=True)
            raise

    def salvar_pedido_transacional(self, cliente_id, data_pedido, itens, total):
        """Salva um novo pedido e seus itens usando uma transação."""
        try:
            # Inicia a transação (commit=False)

            # 1. Insere o pedido principal
            query_pedido = "INSERT INTO pedidos (cliente_id, data, total) VALUES (?, ?, ?)"
            # Pedimos para retornar o ID do pedido inserido
            pedido_id = execute_query(query_pedido, (cliente_id, data_pedido, total), commit=False,
                                      fetch_last_row_id=True)

            if not pedido_id:
                raise Exception("Não foi possível obter o ID do novo pedido.")

            # 2. Insere os itens
            query_item = "INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit) VALUES (?, ?, ?, ?)"
            for item in itens:
                execute_query(query_item, (pedido_id, item['produto'], item['quantidade'], item['preco_unit']),
                              commit=False)

            # 3. Efetiva a transação
            execute_query("COMMIT", commit=False)  # O commit=False aqui apenas executa o comando "COMMIT"

            log.info(f"Pedido {pedido_id} salvo com sucesso em transação.")

        except Exception as e:
            log.error(f"Erro na transação de salvar pedido: {e}", exc_info=True)
            try:
                # Tenta reverter a transação em caso de erro
                execute_query("ROLLBACK", commit=False)
                log.warning("Transação de salvar pedido revertida (ROLLBACK).")
            except Exception as re:
                log.critical(f"Falha ao reverter (ROLLBACK) transação: {re}", exc_info=True)
            raise  # Levanta a exceção original para o controlador

    def editar_pedido_transacional(self, pedido_id, cliente_id, data_pedido, itens, total):
        """Atualiza um pedido e seus itens usando uma transação."""
        try:
            # 1. Atualiza o pedido principal
            query_pedido_update = "UPDATE pedidos SET cliente_id = ?, data = ?, total = ? WHERE id = ?"
            execute_query(query_pedido_update, (cliente_id, data_pedido, total, pedido_id), commit=False)

            # 2. Exclui os itens antigos
            query_delete_itens = "DELETE FROM itens_pedido WHERE pedido_id = ?"
            execute_query(query_delete_itens, (pedido_id,), commit=False)

            # 3. Insere os novos itens (ou itens editados)
            query_insert_item = "INSERT INTO itens_pedido (pedido_id, produto, quantidade, preco_unit) VALUES (?, ?, ?, ?)"
            for item in itens:
                execute_query(query_insert_item, (pedido_id, item['produto'], item['quantidade'], item['preco_unit']),
                              commit=False)

            # 4. Efetiva a transação
            execute_query("COMMIT", commit=False)

            log.info(f"Pedido {pedido_id} editado com sucesso em transação.")

        except Exception as e:
            log.error(f"Erro na transação de editar pedido: {e}", exc_info=True)
            try:
                execute_query("ROLLBACK", commit=False)
                log.warning(f"Transação de editar pedido {pedido_id} revertida (ROLLBACK).")
            except Exception as re:
                log.critical(f"Falha ao reverter (ROLLBACK) transação de edição: {re}", exc_info=True)
            raise

    def delete_pedido_transacional(self, pedido_id):
        """Exclui um pedido e todos os seus itens (transacional)."""
        try:
            # 1. Exclui os itens (devido à FK, fazemos isso primeiro)
            query_delete_itens = "DELETE FROM itens_pedido WHERE pedido_id = ?"
            execute_query(query_delete_itens, (pedido_id,), commit=False)

            # 2. Exclui o pedido principal
            query_delete_pedido = "DELETE FROM pedidos WHERE id = ?"
            execute_query(query_delete_pedido, (pedido_id,), commit=False)

            # 3. Efetiva
            execute_query("COMMIT", commit=False)
            log.info(f"Pedido {pedido_id} e seus itens excluídos com sucesso.")

        except Exception as e:
            log.error(f"Erro na transação de excluir pedido: {e}", exc_info=True)
            try:
                execute_query("ROLLBACK", commit=False)
                log.warning(f"Transação de excluir pedido {pedido_id} revertida (ROLLBACK).")
            except Exception as re:
                log.critical(f"Falha ao reverter (ROLLBACK) transação de exclusão: {re}", exc_info=True)
            raise

