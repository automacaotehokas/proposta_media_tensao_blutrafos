# services/document/pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from babel import numbers
from io import BytesIO
from typing import Dict, List, Any


def gerar_pdf(dados_iniciais: Dict, impostos: Dict, itens_configurados: List[Dict]) -> BytesIO:
    """Gera o documento PDF com os dados fornecidos"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=5*mm,
        leftMargin=5*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Adiciona elementos ao documento
    elements.extend(_criar_cabecalho(dados_iniciais, styles))
    elements.extend(_criar_secao_variaveis(impostos, itens_configurados, styles))
    elements.extend(_criar_tabela_itens(itens_configurados, styles))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def _criar_cabecalho(dados: Dict, styles: Dict) -> List:
    """Cria os elementos do cabeçalho do PDF"""
    elementos = [
        Paragraph(f"Proposta: BT-{dados.get('bt', '')}-Rev{dados.get('rev', '')}", 
                    styles['Heading1']),
        Paragraph("<b>Dados da Proposta:</b>", styles['Heading2'])
    ]
    
    campos = [
        ('Cliente', dados.get('cliente')),
        ('Nome do Cliente', dados.get('nomeCliente')),
        ('Telefone', dados.get('fone')),
        ('Email', dados.get('email')),
        ('BT', dados.get('bt')),
        ('Obra', dados.get('obra')),
        ('Concessionária', dados.get('concessionaria')),
        ('Aplicação', dados.get('aplicacao')),
        ('Data', f"{dados.get('dia')}/{dados.get('mes')}/{dados.get('ano')}"),
        ('Revisão', dados.get('rev')),
        ('Local', dados.get('local_frete'))
    ]
    
    for campo, valor in campos:
        elementos.append(
            Paragraph(f"<b>{campo}:</b> {valor}", styles['Normal'])
        )
    
    elementos.append(Spacer(1, 12))
    return elementos

def _criar_secao_variaveis(impostos: Dict, itens_configurados: List[Dict], styles: Dict) -> List:
    """Cria a seção de variáveis do PDF"""
    elementos = [
        Paragraph("<b>Percentuais Considerados:</b>", styles['Heading2']),
        Paragraph(f"<b>Contribuinte:</b> {impostos.get('contribuinte_icms', '')}", styles['Normal']),
        Paragraph(f"<b>Lucro:</b> {impostos.get('lucro', 0):.2f}%", styles['Normal']),
        Paragraph(f"<b>ICMS:</b> {impostos.get('icms', 0):.2f}%", styles['Normal']),
        Paragraph(f"<b>Frete:</b> {impostos.get('frete', 0):.2f}%", styles['Normal']),
        Paragraph(f"<b>Comissão:</b> {impostos.get('comissao', 0):.2f}%", styles['Normal']),
        Paragraph(f"<b>DIFAL:</b> {impostos.get('difal', 0):.2f}%", styles['Normal']),
        Paragraph(f"<b>F.pobreza:</b> {impostos.get('f_pobreza', 0):.2f}%", styles['Normal']),
        Paragraph(f"<b>Local Frete:</b> {impostos.get('local_frete_itens', '')}", styles['Normal'])
    ]

    # Mapeamento de percentuais por classe de tensão
    voltage_class_percentage = {
        "15 kV": 0,
        "24 kV": 30,
        "36 kV": 50
    }

    # Adicionar percentual para cada item
    for idx, item in enumerate(itens_configurados, start=1):
        classe_tensao = item.get('classe_tensao', '')
        percentual = voltage_class_percentage.get(classe_tensao, 'Não especificado')
        if item.get('IP') == "00":
            percentual = 0
        elementos.append(
            Paragraph(f"<b>% Caixa Item {idx}:</b> {percentual}%", styles['Normal'])
        )

    elementos.append(Spacer(1, 12))
    return elementos


def _criar_tabela_itens(itens_configurados: List[Dict], styles: Dict) -> List:
    """Cria a tabela de itens do PDF"""
    elementos = [
        Paragraph("<b>Itens Configurados</b>", styles['Heading2'])
    ]

    # Estilo para células da tabela
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=0,
        spaceAfter=0,
        spaceBefore=0,
    )

    # Cabeçalho da tabela
    data = [['Cód. Proj Trafo', 'Cód. Proj Caixa', 'Descrição', 'K', 'IP', 
                'Qtde', 'Preço Unitário', 'Preço Total']]

    # Estilo para o cabeçalho
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=1,
        textColor=colors.white,
        spaceAfter=0,
        spaceBefore=0,
    )

    data[0] = [Paragraph(cell, header_style) for cell in data[0]]
    total_geral = 0

    # Preenchimento dos dados
    for item in itens_configurados:
        preco_unitario = float(item.get('Preço Unitário', 0) or 0)
        quantidade = float(item.get('Quantidade', 0) or 0)
        preco_total = preco_unitario * quantidade
        total_geral += preco_total

        data.append([
            item.get('cod_proj_custo', ''),
            item.get('cod_proj_caixa', '') if item.get('IP') != "00" else "N/A",
            Paragraph(item.get('Descrição', ''), table_cell_style),
            str(item.get('Fator K', '')),
            str(item.get('IP', '')),
            str(quantidade),
            numbers.format_currency(preco_unitario, 'BRL', locale='pt_BR'),
            numbers.format_currency(preco_total, 'BRL', locale='pt_BR')
        ])

    # Criação da tabela
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00543C')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (2, 1), (2, -1), 'LEFT')
    ]))

    elementos.append(table)
    elementos.append(
        Paragraph(f"<b>Total: {numbers.format_currency(total_geral, 'BRL', locale='pt_BR')}</b>", 
                    styles['Heading2'])
    )

    return elementos