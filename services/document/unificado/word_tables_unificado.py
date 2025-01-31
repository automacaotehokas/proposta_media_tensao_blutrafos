from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from typing import Dict, List
import logging
from .word_formatter_unificado import *

logger = logging.getLogger(__name__)

def create_header(row, headers, is_main_header=True):
    """
    Cria o cabeçalho da tabela com o título especificado
    """
    for idx, header_text in enumerate(headers):
        cell = row.cells[idx]
        paragraph = cell.paragraphs[0]
        paragraph.clear()
        run = paragraph.add_run(header_text)
        run.font.name = 'Calibri Light (Títulos)'
        run.font.size = Pt(11)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        
        # Mesclar células para "Dados Técnicos" no cabeçalho principal
        if is_main_header and idx == 2:
            end_merge = 6
            row.cells[2].merge(row.cells[end_merge])
        
        apply_paragraph_formatting(paragraph, alignment='center')
        set_cell_shading(cell, '00543C')
        add_double_borders(cell)
    return row

def format_decimal_value(value):
    """
    Formata valores Decimal ou numéricos para string
    """
    if str(value).startswith('Decimal'):
        # Remove 'Decimal(' e ')' e converte para float
        value = float(str(value).replace('Decimal(\'', '').replace('\')', ''))
    return str(value)

def fill_item_row_mt(row, item, idx):
    """
    Preenche uma linha da tabela MT com os dados formatados corretamente
    """
    try:
        # Formatação da potência
        potencia = item.get('Potência', '')
        if isinstance(potencia, str) and 'Decimal' in potencia:
            potencia = float(potencia.replace('Decimal(\'', '').replace('\')', ''))
        potencia_formatada = f"{int(float(format_decimal_value(potencia)))} kVA" if potencia else ''

        # Formatação das tensões
        tensao_primaria = format_decimal_value(item.get('Tensão Primária', ''))
        tensao_secundaria = format_decimal_value(item.get('Tensão Secundária', ''))
        tensoes = f"{tensao_primaria}/0,{tensao_secundaria}kV" if tensao_primaria and tensao_secundaria else ''

        # Preparar dados das células
        cells_data = [
            str(idx),  # Item
            str(item.get("Quantidade", "")),  # Quantidade
            potencia_formatada,  # Potência formatada
            str(item.get("Fator K", "")),  # Fator K
            tensoes,  # Tensões formatadas
            str(item.get("IP", "")),  # IP
            str(item.get("Perdas", "")),  # Perdas
            f"R$ {float(format_decimal_value(item.get('Preço Unitário', 0))):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),  # Preço Unitário
            f"R$ {float(format_decimal_value(item.get('Preço Total', 0))):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # Preço Total
        ]

        # Preencher as células
        for cell_idx, cell_text in enumerate(cells_data):
            cell = row.cells[cell_idx]
            paragraph = cell.paragraphs[0]
            paragraph.clear()
            run = paragraph.add_run(str(cell_text))  # Garantir que é string
            run.font.name = 'Calibri Light (Títulos)'
            run.font.size = Pt(11)
            apply_paragraph_formatting(paragraph, alignment='center')
            add_double_borders(cell)

    except Exception as e:
        logger.error(f"Erro ao preencher linha MT: {e}")
        logger.error(f"Item causando erro: {item}")
        raise

def fill_item_row_bt(row, item, idx):
    """
    Preenche uma linha da tabela BT com os dados formatados corretamente
    """
    cells_data = [
        str(idx),
        str(item.get("Quantidade", "")),
        str(item.get("Produto", "")),
        str(item.get("Potência", "")),
        str(item.get("Fator K", "")),
        f"{item.get('Tensão Primária', '')}/{item.get('Tensão Secundária', '')}V",
        str(item.get("IP", "")),
        f"R$ {float(item.get('Preço Unitário', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"R$ {float(item.get('Preço Total', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    ]

    for cell_idx, cell_text in enumerate(cells_data):
        cell = row.cells[cell_idx]
        paragraph = cell.paragraphs[0]
        paragraph.clear()
        run = paragraph.add_run(cell_text)
        run.font.name = 'Calibri Light (Títulos)'
        run.font.size = Pt(11)
        apply_paragraph_formatting(paragraph, alignment='center')
        add_double_borders(cell)

def create_custom_table(doc, itens_mt, itens_bt, observacao):
    """
    Cria uma tabela unificada para produtos MT e BT
    """
    # Calcular número total de linhas necessárias
    num_linhas = 0
    
    if itens_mt:
        num_linhas += 1  # Cabeçalho MT "Dados Técnicos"
        num_linhas += len(itens_mt)  # Linhas de itens MT
        num_linhas += 1  # Linha de subtotal MT
        
    if itens_bt:
        num_linhas += 1  # Cabeçalho BT "Dados Técnicos"
        num_linhas += len(itens_bt)  # Linhas de itens BT
        num_linhas += 1  # Linha de subtotal BT
        
    num_linhas += 1  # Linha do total geral
    if observacao:
        num_linhas += 1  # Linha de observação

    # Criar a tabela
    table = doc.add_table(rows=num_linhas, cols=9)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.left_indent = Cm(0)

    # Definir larguras das colunas
    col_widths = [
        Cm(1.0),   # Item
        Cm(1.0),   # Qtd
        Cm(2.5),   # Potência
        Cm(1.0),   # K
        Cm(2.5),   # Tensões
        Cm(1.0),   # IP
        Cm(2.0),   # Perda
        Cm(2.5),   # Preço Unit
        Cm(2.5),   # Preço Total
    ]

    table.autofit = False
    set_column_widths(table, col_widths)
    current_row = 0

    # Seção MT
    if itens_mt:
        logger.debug(f"Processando {len(itens_mt)} itens MT")
        
        # Cabeçalho MT
        header_row = table.rows[current_row]
        for i in range(9):
            cell = header_row.cells[i]
            paragraph = cell.paragraphs[0]
            paragraph.clear()
            
            # Texto especial para coluna "Dados Técnicos"
            if i == 2:
                run = paragraph.add_run("Dados Técnicos do Transformador:")
            else:
                run = paragraph.add_run("")
                
            run.font.name = 'Calibri Light (Títulos)'
            run.font.size = Pt(11)
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            apply_paragraph_formatting(paragraph, alignment='center')
            set_cell_shading(cell, '00543C')
            add_double_borders(cell)
        
        # Mesclar células do cabeçalho
        header_row.cells[2].merge(header_row.cells[6])
        current_row += 1

        # Itens MT
        for idx, item in enumerate(itens_mt, 1):
            row = table.rows[current_row]
            cells_data = [
                str(idx),
                str(item.get("Quantidade", "")),
                f"{format_decimal_value(item.get('Potência', ''))} kVA",
                str(item.get("Fator K", "")),
                f"{item.get('Tensão Primária', '')}/0,{item.get('Tensão Secundária', '')}kV",
                str(item.get("IP", "")),
                str(item.get("Perdas", "")),
                f"R$ {float(item.get('Preço Unitário', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"R$ {float(item.get('Preço Total', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ]
            
            for cell_idx, cell_text in enumerate(cells_data):
                cell = row.cells[cell_idx]
                paragraph = cell.paragraphs[0]
                paragraph.clear()
                run = paragraph.add_run(str(cell_text))
                run.font.name = 'Calibri Light (Títulos)'
                run.font.size = Pt(11)
                apply_paragraph_formatting(paragraph, alignment='center')
                add_double_borders(cell)
            
            current_row += 1

        # Subtotal MT
        subtotal_mt = sum(float(item.get('Preço Total', 0)) for item in itens_mt)
        subtotal_row = table.rows[current_row]
        subtotal_row.cells[0].merge(subtotal_row.cells[6])
        subtotal_row.cells[7].merge(subtotal_row.cells[8])
        
        paragraph_subtotal = subtotal_row.cells[0].paragraphs[0]
        paragraph_subtotal.clear()
        run_subtotal = paragraph_subtotal.add_run("Subtotal MT:")
        run_subtotal.font.name = 'Calibri Light (Títulos)'
        run_subtotal.font.size = Pt(11)
        run_subtotal.bold = True
        
        paragraph_valor = subtotal_row.cells[7].paragraphs[0]
        paragraph_valor.clear()
        run_valor = paragraph_valor.add_run(f"R$ {subtotal_mt:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        run_valor.font.name = 'Calibri Light (Títulos)'
        run_valor.font.size = Pt(11)
        run_valor.bold = True
        
        for idx in [0, 7]:
            cell = subtotal_row.cells[idx]
            apply_paragraph_formatting(cell.paragraphs[0], alignment='center')
            set_cell_shading(cell, '00543C')
            add_double_borders(cell)
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        
        current_row += 1

    # Seção BT
    if itens_bt:
        logger.debug(f"Processando {len(itens_bt)} itens BT")
        
        # Cabeçalho BT
        header_row = table.rows[current_row]
        for i in range(9):
            cell = header_row.cells[i]
            paragraph = cell.paragraphs[0]
            paragraph.clear()
            
            if i == 2:
                run = paragraph.add_run("Dados Técnicos do Transformador:")
            else:
                run = paragraph.add_run("")
                
            run.font.name = 'Calibri Light (Títulos)'
            run.font.size = Pt(11)
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            apply_paragraph_formatting(paragraph, alignment='center')
            set_cell_shading(cell, '00543C')
            add_double_borders(cell)
        
        header_row.cells[2].merge(header_row.cells[6])
        current_row += 1

        # Itens BT
        for idx, item in enumerate(itens_bt, 1):
            row = table.rows[current_row]
            cells_data = [
                str(idx),
                str(item.get("Quantidade", "")),
                str(item.get("Produto", "")),
                str(item.get("Potência", "")),
                str(item.get("Fator K", "")),
                f"{item.get('Tensão Primária', '')}/{item.get('Tensão Secundária', '')}V",
                str(item.get("IP", "")),
                f"R$ {float(item.get('Preço Unitário', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"R$ {float(item.get('Preço Total', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ]
            
            for cell_idx, cell_text in enumerate(cells_data):
                cell = row.cells[cell_idx]
                paragraph = cell.paragraphs[0]
                paragraph.clear()
                run = paragraph.add_run(str(cell_text))
                run.font.name = 'Calibri Light (Títulos)'
                run.font.size = Pt(11)
                apply_paragraph_formatting(paragraph, alignment='center')
                add_double_borders(cell)
            
            current_row += 1

        # Subtotal BT
        subtotal_bt = sum(float(item.get('Preço Total', 0)) for item in itens_bt)
        subtotal_row = table.rows[current_row]
        subtotal_row.cells[0].merge(subtotal_row.cells[6])
        subtotal_row.cells[7].merge(subtotal_row.cells[8])
        
        paragraph_subtotal = subtotal_row.cells[0].paragraphs[0]
        paragraph_subtotal.clear()
        run_subtotal = paragraph_subtotal.add_run("Subtotal BT:")
        run_subtotal.font.name = 'Calibri Light (Títulos)'
        run_subtotal.font.size = Pt(11)
        run_subtotal.bold = True
        
        paragraph_valor = subtotal_row.cells[7].paragraphs[0]
        paragraph_valor.clear()
        run_valor = paragraph_valor.add_run(f"R$ {subtotal_bt:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        run_valor.font.name = 'Calibri Light (Títulos)'
        run_valor.font.size = Pt(11)
        run_valor.bold = True
        
        for idx in [0, 7]:
            cell = subtotal_row.cells[idx]
            apply_paragraph_formatting(cell.paragraphs[0], alignment='center')
            set_cell_shading(cell, '00543C')
            add_double_borders(cell)
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        
        current_row += 1

    # Total Geral
    logger.debug("Processando total geral")
    total_geral = sum(float(item.get('Preço Total', 0)) for item in itens_mt + itens_bt)
    total_row = table.rows[current_row]
    total_row.cells[0].merge(total_row.cells[6])
    total_row.cells[7].merge(total_row.cells[8])

    # Formatação do total geral
    paragraph_total = total_row.cells[0].paragraphs[0]
    paragraph_total.clear()
    run_total = paragraph_total.add_run("Valor Total do Fornecimento:")
    run_total.font.name = 'Calibri Light (Títulos)'
    run_total.font.size = Pt(11)
    run_total.bold = True
    
    paragraph_valor_total = total_row.cells[7].paragraphs[0]
    paragraph_valor_total.clear()
    run_valor_total = paragraph_valor_total.add_run(f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    run_valor_total.font.name = 'Calibri Light (Títulos)'
    run_valor_total.font.size = Pt(11)
    run_valor_total.bold = True

    for idx in [0, 7]:
        cell = total_row.cells[idx]
        apply_paragraph_formatting(cell.paragraphs[0], alignment='center', space_before=Pt(0))
        set_cell_shading(cell, '00543C')
        add_double_borders(cell)
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    current_row += 1

    # Observação
    if observacao:
        logger.debug("Adicionando observação")
        obs_row = table.rows[current_row]
        obs_row.cells[0].merge(obs_row.cells[8])
        obs_cell = obs_row.cells[0]
        paragraph = obs_cell.paragraphs[0]
        paragraph.clear()
        run = paragraph.add_run(f"Obs.: {observacao}")
        run.font.name = 'Calibri Light (Títulos)'
        run.font.size = Pt(11)
        apply_paragraph_formatting(paragraph, alignment='left', space_before=Pt(0))
        add_double_borders(obs_cell)

    logger.info("Tabela criada com sucesso")
    return table

def gerar_escopo_mt(item):
    """
    Gera o texto de escopo para um item MT
    """
    classe_tensao = item.get('classe_tensao', '').replace('kV', '').strip()
    tensao_secundaria = item.get('Tensão Secundária', '').replace('kV', '').strip()
    NBI = item.get('NBI', 'N/A')
    potencia = item.get('Potência', 'N/A')
    
    # Formatar potência se for número
    if isinstance(potencia, (int, float)):
        if float(potencia).is_integer():
            potencia_formatada = f"{int(potencia)} kVA"
        else:
            potencia_formatada = f"{potencia:.1f}".replace('.', ',') + " kVA"
    else:
        potencia_formatada = potencia

    # Calcular tensão secundária
    tensao_secundaria_str = item.get('Tensão Secundária', '0')
    try:
        tensao_secundaria_float = float(tensao_secundaria_str)
        tensao_calculada = tensao_secundaria_float / 1.73
        tensao_calculada_arredondada = round(tensao_calculada)
        tensao_secundaria_arredondada = round(tensao_secundaria_float)
        tensao_secundaria_texto = f"{tensao_secundaria_arredondada}/{tensao_calculada_arredondada}V"
    except ValueError:
        tensao_secundaria_texto = f"{tensao_secundaria_str}V"

    escopo_text = (
        f"Transformador Trifásico **isolado a seco**, Classe de tensão **{classe_tensao}/1,1kV**, "
        f"Marca e Fabricação Blutrafos, Potência: **{potencia_formatada}**, Fator: **K={item.get('Fator K', 'N/A')}**, "
        f"Tensão **Primária**: **{item.get('Tensão Primária', 'N/A')}kV**, Derivações: **{item.get('Derivações', 'N/A')}**, "
        f"Tensão **Secundária**: **{tensao_secundaria_texto}**, Grupo de Ligação: **Dyn-1**, "
        f"Frequência: **60Hz**, NBI: **{NBI}**, Classe de Temperatura: F (155ºC), "
        f"Elevação Temperatura média dos enrolamentos: **100ºC**, Materiais dos enrolamentos: **Alumínio**, "
        f"Altitude de Instalação: **≤1000m**, Temperatura ambiente máxima: 40°C")
    

def gerar_escopo_bt(item):
    """
    Gera o texto de escopo para um item BT
    """
    produto = item.get('Produto', '').upper()
    potencia = item.get('Potência', 'N/A')
    tensao_primaria = item.get('Tensão Primária', 'N/A')
    tensao_secundaria = item.get('Tensão Secundária', 'N/A')
    ip = item.get('IP', 'N/A')
    fator_k = item.get('Fator K', 'N/A')
    material_st = item.get('material', 'Cu')
    material = 'Cobre' if material_st == 'Cu' else 'Alumínio' if material_st == 'Al' else 'N/A'

    if 'ATT' in produto:
        escopo_text = (
            f"Autotransformador trifásico a seco, classe de tensão 1,1kV, Marca e Fabricação Blutrafos, "
            f"Potência {potencia}, Fator K={fator_k}, Tensão Primária: {tensao_primaria}V, "
            f"Tensão Secundária: {tensao_secundaria}V, NBI: N/A, Grupo de Ligação: Yn0, Frequência: 60Hz, "
            f"Enrolamentos impregnados em verniz a vácuo, com resfriamento tipo: AN, Classe de Temperatura materiais isolantes "
            f"AT/BT: F (155ºC), Elevação Temperatura média dos enrolamentos: 100°C, Materiais dos enrolamentos: {material}, "
            f"Regime de Serviço: Contínuo, Temperatura Ambiente máxima: 40°C, Altitude de Instalação: ≤1000m e grau de proteção IP-{ip}. "
            f"Demais características conforme norma ABNT-NBR 5356/11 e acessórios abaixo."
        )
    elif 'TT' in produto:
        escopo_text = (
            f"Transformador isolador trifásico a seco, classe de tensão 1,1kV, Marca e Fabricação Blutrafos, "
            f"Potência {potencia}, Fator K={fator_k}, Tensão Primária: {tensao_primaria}V, "
            f"Tensão Secundária: {tensao_secundaria}V, NBI: N/A, Grupo de Ligação: Dyn1, Frequência: 60Hz, "
            f"Enrolamentos impregnados em verniz a vácuo, com resfriamento tipo: AN, Classe de Temperatura materiais isolantes "
            f"AT/BT: F (155ºC), Elevação Temperatura média dos enrolamentos: 100°C, Materiais dos enrolamentos: {material}, "
            f"Regime de Serviço: Contínuo, Temperatura Ambiente máxima: 40°C, Altitude de Instalação: ≤1000m e grau de proteção IP-{ip}. "
            f"Demais características conforme norma ABNT-NBR 5356/11 e acessórios abaixo."
        )
    elif 'TM' in produto:
        escopo_text = (
            f"Transformador isolador monofásico a seco, classe de tensão 1,1kV, Marca e Fabricação Blutrafos, "
            f"Potência {potencia}, Tensão Primária: {tensao_primaria}V, Tensão Secundária: {tensao_secundaria}V, "
            f"NBI: N/A, Polaridade: Subtrativa, Frequência: 60Hz, Enrolamentos impregnados em verniz a vácuo, "
            f"com resfriamento tipo: AN, Classe de Temperatura materiais isolantes AT/BT: F (155ºC), "
            f"Elevação Temperatura média dos enrolamentos: 100°C, Materiais dos enrolamentos: {material}, "
            f"Regime de Serviço: Contínuo, Temperatura Ambiente máxima: 40°C, Altitude de Instalação: <1000m, "
            f"grau de proteção IP-{ip}, Fator K={fator_k}. Demais características conforme norma ABNT-NBR 5356/11 e acessórios abaixo."
        )
    else:
        logger.error(f"Produto não identificado: {produto}")
        escopo_text = "Produto não identificado. Verifique o item e os dados fornecidos."

    return escopo_text

def create_custom_table_escopo(doc, itens_mt, itens_bt):
    """
    Cria a tabela de escopo unificada para produtos MT e BT
    """
    todos_itens = itens_mt + itens_bt
    table = doc.add_table(rows=len(todos_itens) + 1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    set_table_left_indent(table, 0)
    table.left_indent = Cm(0)
    table.autofit = False

    col_widths = [Cm(1.5), Cm(15.0)]
    set_column_widths(table, col_widths)

    # Cabeçalho
    header_row = table.rows[0]
    header_data = ["Item", "Escopo do Fornecimento:"]

    for idx, cell in enumerate(header_row.cells):
        cell.text = header_data[idx]
        paragraph = cell.paragraphs[0]
        run = paragraph.runs[0]
        run.font.name = 'Calibri Light (T)'
        run.font.size = Pt(11)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        apply_paragraph_formatting(paragraph, alignment='center')
        set_cell_shading(cell, '00543C')
        add_double_borders(cell)

    current_row = 1

    # Processar itens MT
    for idx, item in enumerate(itens_mt, start=1):
        row = table.rows[current_row]
        row.cells[0].text = str(idx)
        apply_paragraph_formatting(row.cells[0].paragraphs[0], alignment='center')
        add_double_borders(row.cells[0])

        escopo_text = gerar_escopo_mt(item)
        escopo_paragraph = row.cells[1].paragraphs[0]
        escopo_paragraph.text = escopo_text

        # Aplicar formatação
        escopo_paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in escopo_paragraph.runs:
            run.font.name = 'Calibri Light (Título)'
            run.font.size = Pt(10)
        
        add_double_borders(row.cells[1])
        current_row += 1

    # Processar itens BT
    for idx, item in enumerate(itens_bt, start=len(itens_mt)+1):
        row = table.rows[current_row]
        row.cells[0].text = str(idx)
        apply_paragraph_formatting(row.cells[0].paragraphs[0], alignment='center')
        add_double_borders(row.cells[0])

        escopo_text = gerar_escopo_bt(item)
        escopo_paragraph = row.cells[1].paragraphs[0]
        escopo_paragraph.text = escopo_text

        # Aplicar formatação
        escopo_paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in escopo_paragraph.runs:
            run.font.name = 'Calibri Light (Título)'
            run.font.size = Pt(10)
        
        add_double_borders(row.cells[1])
        current_row += 1

    return table