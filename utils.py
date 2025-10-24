import re
from tkinter import messagebox


def validate_not_empty(field_value, field_name, parent_window=None):
    """
    Verifica se um campo (após remover espaços) não está vazio.
    Exibe um messagebox de erro se estiver vazio.

    :param field_value: O valor (string) a ser testado.
    :param field_name: O nome do campo para a mensagem de erro (ex: "Nome").
    :param parent_window: A janela pai para o messagebox.
    :return: True se válido, False se inválido.
    """
    if not field_value.strip():
        messagebox.showerror(
            "Erro de Validação",
            f"O campo '{field_name}' é obrigatório.",
            parent=parent_window
        )
        return False
    return True


def validate_email_format(email, parent_window=None):
    """
    Verifica se o e-mail (se preenchido) possui um formato simples (@ e .).
    Permite campo vazio.

    :param email: A string do e-mail.
    :param parent_window: A janela pai para o messagebox.
    :return: True se válido (ou vazio), False se inválido.
    """
    email = email.strip()
    # Permite campo vazio
    if email and ('@' not in email or '.' not in email):
        messagebox.showerror(
            "Erro de Validação",
            "Formato de e-mail inválido. Deve conter '@' e '.'.",
            parent=parent_window
        )
        return False
    return True


def validate_telefone_format(telefone, parent_window=None):
    """
    Verifica se o telefone (se preenchido) contém apenas 8 a 15 dígitos.
    Permite campo vazio.

    :param telefone: A string do telefone.
    :param parent_window: A janela pai para o messagebox.
    :return: True se válido (ou vazio), False se inválido.
    """
    telefone = telefone.strip()
    # Permite campo vazio
    # re.fullmatch garante que a string *inteira* bate com o padrão
    if telefone and not re.fullmatch(r"\d{8,15}", telefone):
        messagebox.showerror(
            "Erro de Validação",
            "Telefone inválido. Deve conter apenas números (de 8 a 15 dígitos).",
            parent=parent_window
        )
        return False
    return True


def validate_positive_integer(value_str, field_name, parent_window=None):
    """
    Verifica se a string é um inteiro positivo.
    Usado para Quantidade.

    :param value_str: A string do campo.
    :param field_name: O nome do campo (ex: "Quantidade").
    :param parent_window: A janela pai para o messagebox.
    :return: O inteiro (se válido), ou None se inválido.
    """
    try:
        value = int(value_str)
        if value <= 0:
            raise ValueError(f"{field_name} deve ser positivo")
        return value
    except ValueError:
        messagebox.showerror(
            "Erro de Validação",
            f"{field_name} inválida. Deve ser um número inteiro positivo.",
            parent=parent_window
        )
        return None


def validate_positive_float(value_str, field_name, parent_window=None):
    """
    Verifica se a string é um float positivo (aceita vírgula).
    Usado para Preço.

    :param value_str: A string do campo.
    :param field_name: O nome do campo (ex: "Preço Unitário").
    :param parent_window: A janela pai para o messagebox.
    :return: O float (se válido), ou None se inválido.
    """
    try:
        # Substitui vírgula por ponto para R$
        value_str_normalized = value_str.strip().replace(',', '.')
        value = round(float(value_str_normalized), 2)
        if value <= 0:
            raise ValueError(f"{field_name} deve ser positivo")
        return value
    except ValueError:
        messagebox.showerror(
            "Erro de Validação",
            f"{field_name} inválido. Deve ser um número positivo.",
            parent=parent_window
        )
        return None


if __name__ == "__main__":
    # Teste rápido (requer uma janela root para os messageboxes)
    print("Testando funções de utilidade (requer interação manual para erros):")

    root = tk.Tk()
    root.withdraw()  # Esconde a janela root principal

    print("Testando 'validate_not_empty':")
    print(f"'  ' -> {validate_not_empty('  ', 'Teste Vazio', root)}")  # Deve falhar (False)
    print(f"'Olá' -> {validate_not_empty('Olá', 'Teste Cheio', root)}")  # Deve passar (True)

    print("\nTestando 'validate_email_format':")
    print(f"'' -> {validate_email_format('', root)}")  # Deve passar (True)
    print(f"'teste@email.com' -> {validate_email_format('teste@email.com', root)}")  # Deve passar (True)
    print(f"'teste.com' -> {validate_email_format('teste.com', root)}")  # Deve falhar (False)

    print("\nTestando 'validate_telefone_format':")
    print(f"'' -> {validate_telefone_format('', root)}")  # Deve passar (True)
    print(f"'12345678' -> {validate_telefone_format('12345678', root)}")  # Deve passar (True)
    print(f"'1234567' -> {validate_telefone_format('1234567', root)}")  # Deve falhar (False)
    print(f"'12345abc' -> {validate_telefone_format('12345abc', root)}")  # Deve falhar (False)

    print("\nTestando 'validate_positive_integer':")
    print(f"'5' -> {validate_positive_integer('5', 'Qtd', root)}")  # Deve passar (5)
    print(f"'0' -> {validate_positive_integer('0', 'Qtd', root)}")  # Deve falhar (None)
    print(f"'abc' -> {validate_positive_integer('abc', 'Qtd', root)}")  # Deve falhar (None)

    print("\nTestando 'validate_positive_float':")
    print(f"'10.50' -> {validate_positive_float('10.50', 'Preço', root)}")  # Deve passar (10.5)
    print(f"'10,99' -> {validate_positive_float('10,99', 'Preço', root)}")  # Deve passar (10.99)
    print(f"'-5.0' -> {validate_positive_float('-5.0', 'Preço', root)}")  # Deve falhar (None)

    print("\nTestes concluídos. Feche as janelas de erro, se houver.")

    # Precisamos destruir a root 'escondida'
    root.destroy()
