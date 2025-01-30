from docx.shared import Pt, RGBColor, Cm
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH 
from docx.enum.table import WD_TABLE_ALIGNMENT

def set_row_height(row, height_cm):
    tr = row._tr
    trHeight = OxmlElement('w:trHeight')
    trHeight.set(qn('w:val'), str(int(height_cm * 567)))
    trHeight.set(qn('w:hRule'), 'exact')
    tr.append(trHeight)

def set_column_widths(table, col_widths):
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

def apply_paragraph_formatting(paragraph, alignment='center', space_before=Pt(5), space_after=Pt(0)):
    paragraph_format = paragraph.paragraph_format
    paragraph_format.space_before = space_before
    paragraph_format.space_after = space_after
    paragraph_format.line_spacing = 1
    paragraph.alignment = {'left': 0, 'center': 1, 'right': 2}.get(alignment, 1)

def set_cell_shading(cell, color):
    tc_pr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color)
    tc_pr.append(shd)

def add_double_borders(cell):
    tc = cell._element
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for border_name in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'double')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '000000')
        tcBorders.append(border)
    tcPr.append(tcBorders)

def set_table_left_indent(table, indent):
    tbl_pr = table._tbl.tblPr
    tbl_indent = tbl_pr.xpath("w:tblInd")
    if tbl_indent:
        tbl_indent[0].set(qn('w:w'), str(indent))
        tbl_indent[0].set(qn('w:type'), 'dxa')
    else:
        tbl_indent_element = OxmlElement('w:tblInd')
        tbl_indent_element.set(qn('w:w'), str(indent))
        tbl_indent_element.set(qn('w:type'), 'dxa')
        tbl_pr.append(tbl_indent_element)