import os
import logging

def verificar_produto_ip(itens_configurados):
   logger = logging.getLogger(__name__)
   logger.info(f"Iniciando verificação de {len(itens_configurados)} itens")
   
   resultados = []
   combinacoes_ja_processadas = set()

   for item in itens_configurados:
       try:
           produto = item.get('Produto', '')
           ip = item.get('IP', '')
           potencia_str = item.get('Potência', '0')
           conector = item.get('Conector', '').upper()
           flange = item.get('Flange', 0)

           # Extrair o valor numérico da potência removendo 'kVA' ou outros caracteres
           try:
               # Remove 'kVA', 'kva', espaços e converte para float
               potencia = float(''.join(c for c in potencia_str if c.isdigit() or c == '.'))
               logger.debug(f"Potência extraída: {potencia} (original: {potencia_str})")
           except (ValueError, AttributeError) as e:
               logger.error(f"Erro ao converter potência '{potencia_str}': {str(e)}")
               potencia = 0

           combinacao = (produto, ip, potencia, conector)
           
           logger.debug(f"""
               Processando item:
               Produto: {produto}
               IP: {ip}
               Potência: {potencia} (original: {potencia_str})
               Conector: {conector}
               Flange: {flange}
           """)

           if combinacao in combinacoes_ja_processadas:
               logger.debug(f"Combinação {combinacao} já processada, pulando...")
               continue

           combinacoes_ja_processadas.add(combinacao)

           # Inicializar variáveis
           caminho_imagem = os.path.join('imagens', produto.lower() if produto else '', 'blank')
           titulo = ''

           # Regras de imagens
           if produto == 'ATT':
               if ip == '00':
                   caminho_imagem = os.path.join('imagens', 'att', 'tg3ip00.png')
               elif ip in ['21', '23']:
                   caminho_imagem = os.path.join('imagens', 'att', f'tg3ip21.png')
               titulo = f"Autotransformador – Modelo TG3 - IP {ip}"
           
           elif produto == 'TM':
               if 2.5 <= potencia <= 20:
                   caminho_imagem = os.path.join('imagens', 'tm', 's3.png')
                   titulo = f"Transformador Monofásico – Modelo S3 - IP {ip}"
               elif 0.05 <= potencia <= 2.5 and 'WAGO' in conector:
                   caminho_imagem = os.path.join('imagens', 'tm', 'b2.png')
                   titulo = f"Transformador Monofásico – Modelo B2 - IP {ip}"
               elif 0.05 <= potencia <= 2.5 and 'SINDAL' in conector:
                   caminho_imagem = os.path.join('imagens', 'tm', 'm9.png')
                   titulo = f"Transformador Monofásico – Modelo M9 – IP {ip}"

           elif produto == 'TT':
               if 0.1 <= potencia <= 2 and 'SINDAL' in conector:
                   caminho_imagem = os.path.join('imagens', 'tt', 'tea2.png')
                   titulo = f"Transformador Trifásico – Modelo TEA2 – IP {ip}"
               elif 0.1 <= potencia <= 2 and 'WAGO' in conector:
                   caminho_imagem = os.path.join('imagens', 'tt', 'ta9.png')
                   titulo = f"Transformador Trifásico – Modelo TA9 – IP {ip}"
               elif 2.5 <= potencia <= 50:
                   if ip == '00':
                       caminho_imagem = os.path.join('imagens', 'tt', 'tg3ip00.png')
                   elif ip in ['21', '23']:
                       caminho_imagem = os.path.join('imagens', 'tt', 'tg3ip21.png')
                   titulo = f"Transformador Trifásico – Modelo TG3 - IP {ip}"
               elif 50 <= potencia <= 360:
                   if ip == '00':
                       caminho_imagem = os.path.join('imagens', 'tt', 'tg12ip00.png')
                   elif ip in ['21', '23']:
                       caminho_imagem = os.path.join('imagens', 'tt', 'tg12ip21.png')
                   elif ip in ['54'] and flange == 1:
                       caminho_imagem = os.path.join('imagens', 'tt', 'tg12ip541flange.png')
                   elif ip in ['54'] and flange == 2:
                       caminho_imagem = os.path.join('imagens', 'tt', 'tg12ip542flange.png')
                   titulo = f"Transformador Trifásico – Modelo TG12 - IP {ip}"

           logger.debug(f"Caminho de imagem definido: {caminho_imagem}")
           logger.debug(f"Título definido: {titulo}")

           resultados.append({
               'Produto': produto,
               'IP': ip,
               'Potência': potencia,
               'Conector': conector,
               'CaminhoImagem': caminho_imagem,
               'Titulo': titulo
           })

       except Exception as e:
           logger.error(f"Erro ao processar item: {str(e)}", exc_info=True)
           continue

   logger.info(f"Processamento concluído. {len(resultados)} resultados gerados")
   return resultados


def determinar_condicoes_pagamento(itens_configurados):
    preco_total = sum(item['Preço Total'] for item in itens_configurados)  # Soma de todos os preços totais
    if preco_total <= 2500:
        return ["100% com o pedido de compra."]
    else:
        return [
            "50% com o pedido de compra.",
            "50% com o aviso de pronto."
        ]