"""
Export_Utils.py (Camada de Utilitários de Exportação)

Contém a lógica para gerar arquivos CSV e PDF (usando reportlab)
e para abrir os arquivos gerados no sistema operacional.
"""

import csv
import webbrowser
import os
import pathlib
import datetime
from typing import List, Dict, Any, Optional, Tuple

# Importações do ReportLab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


# =============================================================================
# === HELPER PARA GERENCIAR ARQUIVOS ===
# =============================================================================

def _get_export_filepath(prefix: str, extension: str) -> str:
    """
    Cria um caminho de arquivo padronizado na pasta 'exports'
    com um timestamp.
    Ex: exports/Pedido_20251111_153045.pdf
    """
    # Garante que a pasta 'exports' exista
    export_dir = "exports"
    pathlib.Path(export_dir).mkdir(parents=True, exist_ok=True)

    # Cria um nome de arquivo único com timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.{extension}"

    filepath = os.path.join(export_dir, filename)
    return filepath


def open_file_externally(filepath: str):
    """
    Abre um arquivo (PDF, CSV) no programa padrão do SO
    (Windows, macOS, Linux).
    """
    print(f"INFO [export_utils]: Tentando abrir o arquivo: {filepath}")
    try:
        # Converte o caminho para um URI (necessário para compatibilidade)
        file_uri = pathlib.Path(filepath).absolute().as_uri()
        webbrowser.open(file_uri)
    except Exception as e:
        print(f"ERRO [export_utils.open_file]: Não foi possível abrir o arquivo: {e}")
        # (Não mostramos messagebox aqui, o main.py já mostrou)


# =============================================================================
# === EXPORTAÇÃO DE PEDIDO ÚNICO ===
# =============================================================================

def export_to_csv(pedido_info: Dict[str, Any], itens_list: List[Dict[str, Any]]) -> Optional[str]:
    """
    Exporta os detalhes de um único pedido para um arquivo CSV.

    :param pedido_info: Dicionário com os dados do pedido/cliente.
    :param itens_list: Lista de dicionários, um para cada item.
    :return: O caminho do arquivo gerado ou None se falhar.
    """
    filepath = _get_export_filepath(f"Pedido_{pedido_info.get('id', 'desconhecido')}", "csv")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')  # Usando ';' como delimitador (comum no Brasil)

            # --- Cabeçalho do Pedido ---
            writer.writerow(["DADOS DO PEDIDO"])
            writer.writerow(["ID Pedido:", pedido_info.get('id')])
            writer.writerow(["Data:", pedido_info.get('data')])
            writer.writerow(["Total:", f"R$ {pedido_info.get('total', 0.0):.2f}"])
            writer.writerow([])  # Linha em branco

            # --- Cabeçalho do Cliente ---
            writer.writerow(["DADOS DO CLIENTE"])
            writer.writerow(["Nome:", pedido_info.get('cliente_nome')])
            writer.writerow(["E-mail:", pedido_info.get('email')])
            writer.writerow(["Telefone:", pedido_info.get('telefone')])
            writer.writerow([])  # Linha em branco

            # --- Itens do Pedido ---
            writer.writerow(["ITENS DO PEDIDO"])
            writer.writerow(["Produto", "Quantidade", "Preço Unitário (R$)", "Subtotal (R$)"])

            for item in itens_list:
                subtotal = item.get('quantidade', 0) * item.get('preco_unit', 0.0)
                writer.writerow([
                    item.get('produto'),
                    item.get('quantidade'),
                    f"{item.get('preco_unit', 0.0):.2f}",
                    f"{subtotal:.2f}"
                ])

        return filepath

    except Exception as e:
        print(f"ERRO [export_utils.export_to_csv]: {e}")
        raise e  # Re-levanta o erro para o main.py


def export_to_pdf(pedido_info: Dict[str, Any], itens_list: List[Dict[str, Any]]) -> Optional[str]:
    """
    Exporta os detalhes de um único pedido para um arquivo PDF simples.

    :param pedido_info: Dicionário com os dados do pedido/cliente.
    :param itens_list: Lista de dicionários, um para cada item.
    :return: O caminho do arquivo gerado ou None se falhar.
    """
    filepath = _get_export_filepath(f"Pedido_{pedido_info.get('id', 'desconhecido')}", "pdf")

    try:
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4  # (w, h)

        # Posição inicial (topo da página, com margem)
        y = height - 2 * cm  # Começa a 2cm do topo
        margin_left = 2 * cm

        # --- Título ---
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin_left, y, f"Detalhes do Pedido ID: {pedido_info.get('id')}")
        y -= 1.5 * cm  # Espaço após o título

        # --- Dados do Cliente ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_left, y, "Dados do Cliente")
        y -= 0.7 * cm

        c.setFont("Helvetica", 11)
        c.drawString(margin_left, y, f"Nome: {pedido_info.get('cliente_nome', 'N/A')}")
        y -= 0.6 * cm
        c.drawString(margin_left, y, f"E-mail: {pedido_info.get('email', 'N/A')}")
        y -= 0.6 * cm
        c.drawString(margin_left, y, f"Telefone: {pedido_info.get('telefone', 'N/A')}")
        y -= 1 * cm  # Espaço

        # --- Dados do Pedido ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_left, y, "Dados do Pedido")
        y -= 0.7 * cm

        c.setFont("Helvetica", 11)
        c.drawString(margin_left, y, f"Data: {pedido_info.get('data', 'N/A')}")
        y -= 0.6 * cm

        # --- Tabela de Itens ---
        y -= 1 * cm  # Espaço
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_left, y, "Itens do Pedido")
        y -= 0.8 * cm

        # Preparando dados da tabela
        data = [
            ["Produto", "Qtd", "Preço Unit. (R$)", "Subtotal (R$)"]  # Cabeçalho
        ]

        # Estilos do Cabeçalho
        header_style = ('GRID', (0, 0), (-1, 0), 1, colors.black)
        header_font = ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')

        # Adiciona os itens
        total_pedido = 0.0
        for item in itens_list:
            qtd = item.get('quantidade', 0)
            preco = item.get('preco_unit', 0.0)
            subtotal = qtd * preco
            total_pedido += subtotal
            data.append([
                item.get('produto', 'N/A'),
                str(qtd),
                f"{preco:.2f}",
                f"{subtotal:.2f}"
            ])

        # Adiciona a linha do Total
        data.append([
            "", "",  # Células vazias
            "TOTAL:",  # Label
            f"R$ {total_pedido:.2f}"  # Valor
        ])

        # Estilos do Total
        total_style = ('GRID', (2, -1), (3, -1), 1, colors.black)
        total_font_bold = ('FONTNAME', (2, -1), (2, -1), 'Helvetica-Bold')
        total_align = ('ALIGN', (2, -1), (2, -1), 'RIGHT')

        # Criando a Tabela (Platypus)
        table = Table(data, colWidths=[8 * cm, 2 * cm, 3.5 * cm, 3.5 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            header_style,
            ('GRID', (0, 1), (-1, -2), 1, colors.grey),  # Grid dos itens
            total_style,
            total_font_bold,
            total_align,
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Alinha Qtd, Preço, Subtotal
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Alinha Produto
        ]))

        # Desenha a tabela na tela (Canvas)
        table.wrapOn(c, width - (2 * margin_left), height)  # Calcula o tamanho
        table_height = table._height
        table.drawOn(c, margin_left, y - table_height)  # Posiciona

        c.save()  # Salva o arquivo PDF
        return filepath

    except Exception as e:
        print(f"ERRO [export_utils.export_to_pdf]: {e}")
        raise e


# =============================================================================
# === EXPORTAÇÃO DE RELATÓRIO (LISTA) ===
# =============================================================================

def export_list_to_csv(data_list: List[Tuple]) -> Optional[str]:
    """
    Exporta uma lista (do relatório) para um arquivo CSV.

    :param data_list: Lista de tuplas (id, data, cliente, itens_str, total).
    :return: O caminho do arquivo gerado ou None se falhar.
    """
    filepath = _get_export_filepath("Relatorio_Pedidos", "csv")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')

            # Cabeçalho do CSV
            writer.writerow(["ID Pedido", "Data", "Cliente", "Itens (Qtd)", "Total (R$)"])

            # Escreve os dados
            for row in data_list:
                # row = (id, data, cliente, itens_str, total)
                itens_formatados = row[3].replace(",", "; ") if row[3] else "N/A"
                total_formatado = f"{row[4]:.2f}"

                writer.writerow([
                    row[0],  # id
                    row[1],  # data
                    row[2],  # cliente
                    itens_formatados,
                    total_formatado
                ])

        return filepath

    except Exception as e:
        print(f"ERRO [export_utils.export_list_to_csv]: {e}")
        raise e


def export_list_to_pdf(data_list: List[Tuple]) -> Optional[str]:
    """
    Exporta uma lista (do relatório) para um arquivo PDF simples.

    :param data_list: Lista de tuplas (id, data, cliente, itens_str, total).
    :return: O caminho do arquivo gerado ou None se falhar.
    """
    filepath = _get_export_filepath("Relatorio_Pedidos", "pdf")

    try:
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        y = height - 2 * cm
        margin_left = 2 * cm

        # --- Título ---
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin_left, y, "Relatório de Pedidos")
        y -= 1.5 * cm

        # --- Tabela de Itens ---

        # Cabeçalho
        data = [
            ["ID", "Data", "Cliente", "Itens (Qtd)", "Total (R$)"]
        ]

        # Estilos
        header_style = ('GRID', (0, 0), (-1, 0), 1, colors.black)
        header_font = ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')

        # Adiciona os dados
        total_geral = 0.0
        for row in data_list:
            # row = (id, data, cliente, itens_str, total)
            itens_formatados = row[3].replace(",", "; ") if row[3] else "N/A"
            total_formatado = f"{row[4]:.2f}"
            total_geral += row[4]

            data.append([
                str(row[0]),  # id
                row[1],  # data
                row[2],  # cliente
                itens_formatados,
                total_formatado
            ])

        # Adiciona a linha do Total Geral
        data.append([
            "", "", "",  # Células vazias
            "TOTAL GERAL:",  # Label
            f"R$ {total_geral:.2f}"  # Valor
        ])

        # Estilos do Total
        total_style = ('GRID', (3, -1), (4, -1), 1, colors.black)
        total_font_bold = ('FONTNAME', (3, -1), (3, -1), 'Helvetica-Bold')
        total_align = ('ALIGN', (3, -1), (3, -1), 'RIGHT')

        # Criando a Tabela (Platypus)
        # Largura das colunas (precisa somar 17cm, que é A4 (21) - 4cm margens)
        table = Table(data, colWidths=[1.5 * cm, 2.5 * cm, 5 * cm, 5 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            header_style,
            ('GRID', (0, 1), (-1, -2), 1, colors.grey),  # Grid dos itens
            total_style,
            total_font_bold,
            total_align,
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Fonte menor para caber
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinha no topo
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # ID e Data
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),  # Total
        ]))

        # Desenha a tabela
        table.wrapOn(c, width - (2 * margin_left), height)
        table_height = table._height
        table.drawOn(c, margin_left, y - table_height)

        c.save()
        return filepath

    except Exception as e:
        print(f"ERRO [export_utils.export_list_to_pdf]: {e}")
        raise e