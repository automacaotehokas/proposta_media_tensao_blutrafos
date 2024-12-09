import os
from dotenv import load_dotenv
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document
from sharepoint_code import SharePoint  # Certifique-se de ter este módulo
from replace import inserir_tabelas_word  # Certifique-se de ter esta função
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

st.set_page_config(layout="wide")

# Inicialização do session_state
for key in ['local_frete', 'icms', 'contribuinte_icms', 'lucro', 'frete', 'local_frete_itens', 'difal', 'f_pobreza', 'comissao']:
    if key not in st.session_state:
        st.session_state[key] = 0.0 if 'f' in key or 'c' in key else ''  # Ajuste para valores padrão

# Função para verificar se os dados estão completos
def verificar_dados_completos():
    dados_iniciais = st.session_state.get('dados_iniciais', {})
    itens_configurados = st.session_state.get('itens_configurados', [])

    campos_obrigatorios = ['cliente', 'nomeCliente', 'fone', 'email', 'bt', 'dia', 'mes', 'ano', 'rev', 'local_frete']

    for campo in campos_obrigatorios:
        if not dados_iniciais.get(campo):
            return False

    if not itens_configurados:
        return False

    return True

# Função para baixar o template uma vez e reutilizá-lo
def get_template_file():
    local_template_path = "/tmp/Template_Proposta_Comercial.docx"
    
    if not os.path.exists(local_template_path):
        sp = SharePoint()
        template_name = 'Template_Proposta_Comercial.docx'
        local_template_path = sp.download_file(template_name)
    
    return local_template_path

# Função para gerar documento Word
def gerar_documento_word():
    template_path = get_template_file()
    output_filename = f"Proposta Blutrafos nº BT {st.session_state['dados_iniciais']['bt']}-Rev{st.session_state['dados_iniciais']['rev']}.docx"
    
    replacements = {
        '{{CLIENTE}}': str(st.session_state['dados_iniciais'].get('cliente', '')),
        '{{NOMECLIENTE}}': str(st.session_state['dados_iniciais'].get('nomeCliente', '')),
        '{{FONE}}': str(st.session_state['dados_iniciais'].get('fone', '')),
        '{{EMAIL}}': str(st.session_state['dados_iniciais'].get('email', '')),
        '{{BT}}': str(st.session_state['dados_iniciais'].get('bt', '')),
        '{{OBRA}}': str(st.session_state['dados_iniciais'].get('obra', ' ')) if st.session_state['dados_iniciais'].get('obra') else ' ',
        '{{DIA}}': str(st.session_state['dados_iniciais'].get('dia', '')),
        '{{MES}}': str(st.session_state['dados_iniciais'].get('mes', '')),
        '{{ANO}}': str(st.session_state['dados_iniciais'].get('ano', '')),
        '{{REV}}': str(st.session_state['dados_iniciais'].get('rev', '')),
        '{{LOCAL}}': str(st.session_state['dados_iniciais'].get('local_frete', '')),
        '{{LOCALFRETE}}': str(st.session_state['local_frete_itens']),
        '{{ICMS}}': str(st.session_state['icms']).replace('.', ',') + "%",
        '{{IP}}': ', '.join(set(
            str(item['IP']) for item in st.session_state['itens_configurados'] if item['IP'] != '00')),
    '{obra}': '' if not st.session_state['dados_iniciais'].get('obra', '').strip() else 'Obra:'
}

    # Se {{OBRA}} for vazio, também remover {obra}
    if replacements['{{OBRA}}'] == '':
        replacements['{obra}'] = ''

    itens_configurados = st.session_state.get('itens_configurados', [])

    if not itens_configurados:
        st.error("Por favor, preencha todos os itens antes de gerar o documento.")
        return None, None

    buffer = BytesIO()

    try:
        doc = Document(template_path)
        doc = inserir_tabelas_word(doc, itens_configurados, '', replacements)
        doc.save(buffer)
        
        buffer.seek(0)
        return buffer, output_filename
    
    except Exception as e:
        st.error(f"Erro ao gerar o documento: {e}")
        return None, None
# Função para gerar PDF com ReportLab
def gerar_pdf():
    # Cria um buffer para o PDF
    buffer = BytesIO()
    try:
        # Configura o documento
        left_margin = right_margin = 5 * mm  # Margens da página
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=right_margin,
            leftMargin=left_margin,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )
        elements = []
        styles = getSampleStyleSheet()

        # Cálculo da largura disponível
        PAGE_WIDTH, PAGE_HEIGHT = A4
        available_width = PAGE_WIDTH - doc.leftMargin - doc.rightMargin

        # Dados iniciais
        dados_iniciais = st.session_state['dados_iniciais']
        elementos_dados_iniciais = [
            Paragraph(f"Proposta: BT-{st.session_state['dados_iniciais'].get('bt', '')}-Rev{st.session_state['dados_iniciais'].get('rev', '')}", styles['Heading1']),
            Paragraph("<b>Dados da Proposta :</b>", styles['Heading2']),
            Paragraph(f"<b>Cliente:</b> {dados_iniciais.get('cliente', '')}", styles['Normal']),
            Paragraph(f"<b>Nome do Cliente:</b> {dados_iniciais.get('nomeCliente', '')}", styles['Normal']),
            Paragraph(f"<b>Telefone:</b> {dados_iniciais.get('fone', '')}", styles['Normal']),
            Paragraph(f"<b>Email:</b> {dados_iniciais.get('email', '')}", styles['Normal']),
            Paragraph(f"<b>BT:</b> {dados_iniciais.get('bt', '')}", styles['Normal']),
            Paragraph(f"<b>Obra:</b> {dados_iniciais.get('obra', '')}", styles['Normal']),
            Paragraph(f"<b>Data:</b> {dados_iniciais.get('dia', '')}/{dados_iniciais.get('mes', '')}/{dados_iniciais.get('ano', '')}", styles['Normal']),
            Paragraph(f"<b>Revisão:</b> {dados_iniciais.get('rev', '')}", styles['Normal']),
            Paragraph(f"<b>Local:</b> {dados_iniciais.get('local_frete', '')}", styles['Normal']),
            Spacer(1, 12),
        ]
        elements.extend(elementos_dados_iniciais)

        # Resumo das Variáveis
        elementos_variaveis = [
            Paragraph("<b>Percentuais Considerados :</b>", styles['Heading2']),
            Paragraph(f"<b>Contribuinte:</b> {st.session_state['contribuinte_icms']}", styles['Normal']),
            Paragraph(f"<b>Lucro:</b> {st.session_state['lucro']:.2f}%", styles['Normal']),
            Paragraph(f"<b>ICMS:</b> {st.session_state['icms']:.2f}%", styles['Normal']),
            Paragraph(f"<b>Frete:</b> {st.session_state['frete']:.2f}%", styles['Normal']),
            Paragraph(f"<b>Comissão:</b> {st.session_state['comissao']:.2f}%", styles['Normal']),
            Paragraph(f"<b>DIFAL:</b> {st.session_state['difal']:.2f}%", styles['Normal']),
            Paragraph(f"<b>F.pobreza:</b> {st.session_state['f_pobreza']:.2f}%", styles['Normal']),
            Paragraph(f"<b>Local Frete:</b> {st.session_state['local_frete_itens']}", styles['Normal']),
        ]

        voltage_class_percentage = {
            "15 kV": 0,
            "24 kV": 30,
            "36 kV": 50
        }

        # Adicionar informação de percentual considerado para cada item
        itens_configurados = st.session_state.get('itens_configurados', [])
        for idx, item in enumerate(itens_configurados, start=1):
            # Obter a classe de tensão corretamente
            classe_tensao = item.get('classe_tensao', '')
            percentual_considerado = voltage_class_percentage.get(classe_tensao, 'Não especificado')
            if item['IP'] == 00:
                percentual_considerado = 0
            elementos_variaveis.append(
                Paragraph(f"<b>% Caixa Item {idx}:</b> {percentual_considerado}%", styles['Normal'])
            )

        elementos_variaveis.append(Spacer(1, 12))
        elements.extend(elementos_variaveis)

        # Estilo para as células da tabela
        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=7,
            leading=9,
            alignment=0,  # 0=left, 1=center, 2=right, 4=justify
            spaceAfter=0,
            spaceBefore=0,
        )

        # Tabela de itens configurados (mantendo o formato original)
        data = [['Cód. Proj Trafo', 'Cód. Proj Caixa', 'Descrição', 'K', 'IP', 'Qtde', 'Preço Unitário','Preço Total']]

        # Estilo para o cabeçalho
        header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=7,
            leading=9,
            alignment=1,  # center
            textColor=colors.white,
            spaceAfter=0,
            spaceBefore=0,
        )

        # Substituir os cabeçalhos por Paragraphs para consistência
        data[0] = [Paragraph(cell, header_style) for cell in data[0]]

        total_geral = 0  # Variável para somar o total geral

        for item in itens_configurados:
            # Pega a potência equivalente ou a original se a equivalente estiver vazia
            potencia_item = item.get('Potência Equivalente') or item.get('Potência')
            
            # Verifica o tipo de dado e formata a potência
            if isinstance(potencia_item, (int, float)):
                potencia_str = f"{potencia_item:g} kVA"  # Formata a potência se for número
            else:
                potencia_str = f"{potencia_item} kVA"  # Se for string, apenas concatene com "kVA"
            
            # Mapeia o código de acordo com a potência
            codigo_item = item.get('cod_proj_caixa')  

            if item.get('IP') == "00": 
                codigo_item="N/A"
            # Calcula o preço total do item
            preco_unitario = float(item.get('Preço Unitário', 0) or 0)
            quantidade = float(item.get('Quantidade', 0) or 0)
            preco_total_item = preco_unitario * quantidade
            total_geral += preco_total_item
            
            codigo_custo = item.get('cod_proj_custo') 
            preco_total_str = locale.format_string("%.2f", preco_total_item, grouping=True)
            preco_unitario_str= locale.format_string("%.2f", preco_unitario, grouping=True)
            data.append([
                codigo_custo,
                codigo_item,
                Paragraph(item.get('Descrição', ''), table_cell_style),
                str(item.get('Fator K', '')),
                item.get('IP', ''),
                str(quantidade),
                f"R$ {preco_unitario_str}",  # Substitui vírgula por ponto
                f"R$ {preco_total_str}", 
            ])

        # Definição de pesos para as colunas (ajustado para 6 colunas)
        column_widths_weights = [
            1.5,
            1.5,  # 'Código'
            2.5,    # 'Descrição'
            0.5,  # 'Fator K'
            0.5,  # 'IP'
            0.5,  # 'Quantidade'
            1.5,  # 'Preço Unitário'
             1.5,  # 'Preço TOtal'
        ]
        total_weight = sum(column_widths_weights)
        column_widths = [(available_width * (weight / total_weight)) for weight in column_widths_weights]

        # Cria a tabela
        tabela = Table(data, colWidths=column_widths, repeatRows=1)

        # Estilo da tabela
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00543C')),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
            ('GRID', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            # Alinha à esquerda o texto da coluna 'Descrição'
            ('ALIGN', (2, 1), (2, -1), 'LEFT')
        ])

        tabela.setStyle(table_style)

        elements.append(Paragraph("<b>Itens Configurados</b>", styles['Heading2']))
        elements.append(tabela)

                # Converte o preço total para string, substitui vírgula por ponto
        preco_total_str = locale.format_string("%.2f", preco_total_item, grouping=True)

        # Adiciona a frase de total abaixo da tabela
        elements.append(Paragraph(f"<b>Total: R$ {preco_total_str}</b>", styles['Heading2']))

        # Construir o PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    except Exception as e:
        st.error(f"Erro ao gerar o PDF: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None


# Página para gerar o documento
def pagina_gerar_documento():
    st.title("Resumo")
    st.markdown("---")

    if 'dados_iniciais' not in st.session_state:
        st.error("Por favor, preencha os dados na Pag1 antes de gerar o documento.")
        return

    # Resumo da Pag1 como uma ficha
    st.subheader("Dados Iniciais")
    st.write("**Cliente:**", st.session_state['dados_iniciais'].get('cliente', ''))
    st.write("**Nome do Cliente:**", st.session_state['dados_iniciais'].get('nomeCliente', ''))
    st.write("**Telefone:**", st.session_state['dados_iniciais'].get('fone', ''))
    st.write("**Email:**", st.session_state['dados_iniciais'].get('email', ''))
    st.write("**BT:**", st.session_state['dados_iniciais'].get('bt', ''))
    st.write("**Obra:**", st.session_state['dados_iniciais'].get('obra', ''))
    st.write("**Data:**", f"{st.session_state['dados_iniciais'].get('dia', '')}/{st.session_state['dados_iniciais'].get('mes', '')}/{st.session_state['dados_iniciais'].get('ano', '')}")
    st.write("**Revisão:**", st.session_state['dados_iniciais'].get('rev', ''))
    st.write("**Local:**", st.session_state['dados_iniciais'].get('local_frete', ''))

    st.markdown("---")

    # Mostrar as variáveis comuns apenas uma vez
    st.subheader("Resumo das Variáveis")
    st.write(f"**Contribuinte:** {st.session_state['contribuinte_icms']}")
    st.write(f"**Lucro:** {st.session_state['lucro']:.2f}%")
    st.write(f"**ICMS:** {st.session_state['icms']:.2f}%")
    st.write(f"**Frete:** {st.session_state['frete']:.2f}%")
    st.write(f"**Comissão:** {st.session_state['comissao']:.2f}%")
    st.write(f"**DIFAL:** {st.session_state['difal']:.2f}%")
    st.write(f"**F.pobreza:** {st.session_state['f_pobreza']:.2f}%")
    st.write(f"**Local Frete:** {st.session_state['local_frete_itens']}")

    # Adicionar informação de percentual considerado para cada item
    itens_configurados = st.session_state.get('itens_configurados', [])
    voltage_class_percentage = {
        "15 kV": 0,
        "24 kV": 30,
        "36 kV": 50
    }
    for idx, item in enumerate(itens_configurados, start=1):
        classe_tensao = item.get('classe_tensao', '')
        percentual_considerado = voltage_class_percentage.get(classe_tensao, 'Não especificado')
        # Ajustar o percentual_considerado com base no valor do IP
        if item.get('IP') == "00":
            percentual_considerado = 0
        
        st.write(f"**% Caixa Item {idx}:** {percentual_considerado}%")

    st.write("---")

    # Mostrando os itens configurados
    st.subheader("Itens Configurados")

    # Referenciando o resumo_df armazenado na Pag2
    resumo_df = st.session_state.get('resumo_df', None)
    if resumo_df is not None:
        # Removendo as colunas do resumo_df para refletir as mudanças
        resumo_df = resumo_df.drop(columns=['Tensões', 'Derivações', 'Tensão Primária', 'Tensão Secundária', 'Preço Total'], errors='ignore')
        st.table(resumo_df)  # Exibe a tabela de itens configurados
    else:
        st.write("Nenhum item configurado.")

    # Verificar se todos os dados obrigatórios estão preenchidos
    dados_completos = verificar_dados_completos()
    st.write("O botão abaixo estará disponível após o preenchimento de todos os dados anteriores")

    # Botão para Confirmar e gerar documentos
    if st.button('Confirmar', disabled=not dados_completos):
        if dados_completos:
            # Gerar o documento Word
            buffer_word, output_filename_word = gerar_documento_word()

            # Gerar o PDF
            buffer_pdf = gerar_pdf()

            if buffer_word and buffer_pdf:
                st.success("Documentos gerados com sucesso.")

                # Armazenar os buffers e nomes dos arquivos no session_state
                st.session_state['buffer_word'] = buffer_word
                st.session_state['output_filename_word'] = output_filename_word
                st.session_state['buffer_pdf'] = buffer_pdf
                st.session_state['pdf_filename'] = f"Resumo_Proposta_BT_{st.session_state['dados_iniciais']['bt']}-Rev{st.session_state['dados_iniciais']['rev']}_EXTRATO.pdf"
                st.session_state['downloads_gerados'] = True

            else:
                st.error("Erro ao gerar os documentos.")
        else:
            st.error("Por favor, preencha todos os campos obrigatórios antes de gerar os documentos.")

    # Exibir os botões de download se os documentos foram gerados
    if st.session_state.get('downloads_gerados'):
        st.markdown("### Documentos Gerados:")
        # Documento Word
        col1, col2 = st.columns([6,1])
        with col1:
            output_filename_word = st.session_state.get('output_filename_word', 'Documento Word')
            st.write(f"📄 {output_filename_word}")
        with col2:
            st.download_button(
                label="⬇️",
                data=st.session_state.get('buffer_word'),
                file_name=output_filename_word,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        # Documento PDF
        col1, col2 = st.columns([6,1])
        with col1:
            pdf_filename = st.session_state.get('pdf_filename', 'Documento PDF')
            st.write(f"📄 {pdf_filename}")
        with col2:
            st.download_button(
                label="⬇️",
                data=st.session_state.get('buffer_pdf'),
                file_name=pdf_filename,
                mime="application/pdf"
            )
    else:
        st.warning("Aperte no botão acima para gerar os documentos.")

# Chama a função da página
pagina_gerar_documento()
