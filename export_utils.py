import csv
import os
from typing import List, Dict, Any
from tkinter import filedialog

# --- Imports do ReportLab ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


# --- Funções de Exportação ---

def _get_save_path(title: str, file_filter: List[tuple]) -> str:
    """
    Abre uma caixa de diálogo 'Salvar Como'.
    Retorna o caminho do arquivo ou uma string vazia se cancelado.
    """
    try:
        # 'master' não é um argumento padrão para asksaveasfilename,
        # mas ele funciona bem se o 'parent' for a root.
        # Vamos remover para evitar problemas se a root estiver oculta.
        filepath = filedialog.asksaveasfilename(
            title=title,
            filetypes=file_filter,
            defaultextension=file_filter[0][1]
        )
        return filepath
    except Exception as e:
        print(f"Erro ao obter caminho de salvamento: {e}")
        return ""


def export_to_csv(pedido_info: Dict[str, Any], itens_list: List[Dict[str, Any]]) -> str:
    """
    Exporta os dados de um pedido e seus itens para um arquivo CSV.
    Retorna o caminho do arquivo salvo ou uma string vazia se falhar/cancelar.
    """

    # Define o nome sugerido para o arquivo
    default_filename = f"pedido_{pedido_info.get('id', 'desconhecido')}.csv"

    # Abre a caixa de diálogo 'Salvar Como'
    filepath = _get_save_path(
        title="Salvar Pedido como CSV",
        file_filter=[("CSV files", "*.csv"), ("All files", "*.*")]
    )

    if not filepath:
        return ""  # Usuário cancelou

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # 1. Cabeçalho do Pedido
            writer.writerow(["Pedido ID:", pedido_info.get('id')])
            writer.writerow(["Data:", pedido_info.get('data')])
            writer.writerow(["Cliente:", pedido_info.get('cliente_nome')])

            # Formata o total corretamente
            total_pedido_csv = f"{pedido_info.get('total', 0.0):.2f}".replace('.', ',')
            writer.writerow(["Total:", f"R$ {total_pedido_csv}"])
            writer.writerow([])  # Linha em branco

            # 2. Cabeçalho dos Itens
            writer.writerow(["Itens do Pedido"])
            writer.writerow(["Produto", "Quantidade", "Preço Unitário", "Subtotal"])

            # 3. Itens
            for item in itens_list:
                produto = item.get('produto', 'N/A')
                qtd = item.get('quantidade', 0)
                preco = item.get('preco_unit', 0.0)
                subtotal = qtd * preco

                # Formata para padrão CSV (ex: 1.234,50)
                preco_csv = f"{preco:.2f}".replace('.', ',')
                subtotal_csv = f"{subtotal:.2f}".replace('.', ',')

                writer.writerow([produto, qtd, preco_csv, subtotal_csv])

        return filepath

    except IOError as e:
        print(f"Erro de E/S ao salvar CSV: {e}")
        raise Exception(f"Erro ao salvar arquivo CSV: {e}")
    except Exception as e:
        print(f"Erro inesperado ao exportar CSV: {e}")
        raise Exception(f"Erro inesperado ao exportar CSV: {e}")


def export_to_pdf(pedido_info: Dict[str, Any], itens_list: List[Dict[str, Any]]) -> str:
    """
    Exporta os dados de um pedido e seus itens para um arquivo PDF simples
    usando a biblioteca ReportLab.
    Retorna o caminho do arquivo salvo ou uma string vazia se falhar/cancelar.
    """

    # Define o nome sugerido para o arquivo
    default_filename = f"pedido_{pedido_info.get('id', 'desconhecido')}.pdf"

    # Abre a caixa de diálogo 'Salvar Como'
    filepath = _get_save_path(
        title="Salvar Pedido como PDF",
        file_filter=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )

    if not filepath:
        return ""  # Usuário cancelou

    try:
        # Configuração do Documento
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)

        # 'story' é a lista de 'Flowables' (parágrafos, tabelas, etc.)
        story = []
        styles = getSampleStyleSheet()

        # 1. Título
        story.append(Paragraph(f"Detalhes do Pedido #{pedido_info.get('id', 'N/A')}", styles['h1']))
        story.append(Spacer(1, 0.2 * inch))

        # 2. Informações do Pedido
        story.append(Paragraph(f"<b>Cliente:</b> {pedido_info.get('cliente_nome', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Data:</b> {pedido_info.get('data', 'N/A')}", styles['Normal']))

        # Formata o total
        total_pedido = f"R$ {pedido_info.get('total', 0.0):.2f}"
        story.append(Paragraph(f"<b>Total do Pedido:</b> {total_pedido}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # 3. Título da Tabela de Itens
        story.append(Paragraph("Itens do Pedido", styles['h2']))
        story.append(Spacer(1, 0.1 * inch))

        # 4. Tabela de Itens

        # Dados da tabela (cabeçalho + linhas)
        table_data = [
            ["Produto", "Qtd", "Preço Unit.", "Subtotal"]
        ]

        for item in itens_list:
            qtd = item.get('quantidade', 0)
            preco = item.get('preco_unit', 0.0)
            subtotal = qtd * preco

            # Adiciona a linha formatada
            table_data.append([
                Paragraph(item.get('produto', 'N/A'), styles['Normal']),  # Permite quebra de linha
                str(qtd),
                f"R$ {preco:.2f}",
                f"R$ {subtotal:.2f}"
            ])

        # Cria o objeto Table
        # Define a largura das colunas
        items_table = Table(table_data, colWidths=[3 * inch, 0.5 * inch, 1.2 * inch, 1.2 * inch])

        # Adiciona Estilo à Tabela
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),  # Cor do Header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centraliza tudo
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Alinha produto à esquerda
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header em negrito
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Grid completo
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ])
        items_table.setStyle(style)

        story.append(items_table)

        # 5. Constrói (salva) o PDF
        doc.build(story)

        return filepath

    except Exception as e:
        print(f"Erro ao gerar PDF com ReportLab: {e}")
        raise Exception(f"Erro ao salvar arquivo PDF: {e}")