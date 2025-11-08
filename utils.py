import tkinter as tk


def center_window(window: tk.Toplevel):
    """
    Centraliza uma janela Toplevel em relação à sua janela 'master'.
    """
    window.update_idletasks()  # Garante que as dimensões da janela estejam atualizadas

    # Verifica se o master é a root (Tk) ou outro Toplevel
    if isinstance(window.master, tk.Tk):
        master = window.master
    elif isinstance(window.master, tk.Toplevel):
        master = window.master
    else:
        # Fallback se o 'master' for um Frame (pega a root)
        master = window.winfo_toplevel()

    master_x = master.winfo_x()
    master_y = master.winfo_y()
    master_width = master.winfo_width()
    master_height = master.winfo_height()

    my_width = window.winfo_width()
    my_height = window.winfo_height()

    # Calcula a posição central
    x = master_x + (master_width // 2) - (my_width // 2)
    y = master_y + (master_height // 2) - (my_height // 2)

    # Define apenas a posição
    window.geometry(f'+{x}+{y}')