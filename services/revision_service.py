# services/revision_service.py
import json
import os
from typing import Dict, Any, Optional, Tuple
from proposta_media_tensao_blutrafos.config.databaseMT import DatabaseConfig
from io import BytesIO
from repositories.proposta_repository import PropostaRepository
from models.proposta import Proposta
import streamlit as st 
from decimal import Decimal


class RevisionService:
    @staticmethod
    def salvar_revisao(dados: Dict[str, Any], files: Dict[str, BytesIO]) -> bool:
        """Salva uma revisão no banco de dados e os arquivos no sistema"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            
            print("Dados iniciais:", dados['dados_iniciais'])  # Debug
            
            # Verifica se precisa criar nova proposta
            id_proposta = dados['dados_iniciais'].get('id_proposta')
            if not id_proposta or id_proposta == '':
                try:
                    proposta = Proposta.create_new(dados['dados_iniciais'])
                    id_proposta = PropostaRepository.criar_proposta(proposta)
                    dados['dados_iniciais']['id_proposta'] = id_proposta
                    print("Nova proposta criada:", id_proposta)
                except Exception as e:
                    print(f"Erro ao criar proposta: {str(e)}")
                    raise

            valor_total = float(sum(float(item.get('Preço Total', 0)) 
                            for item in dados['itens_configurados']))
            numero_revisao = int(dados['dados_iniciais'].get('rev', '00'))
            print(f"Valor total: {valor_total}, Revisão: {numero_revisao}")

            word_path, pdf_path = RevisionService._salvar_arquivos(
                str(dados['dados_iniciais']['bt']),
                numero_revisao,
                files
            )
            print(f"Arquivos salvos: Word={word_path}, PDF={pdf_path}")

            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id_revisao::text
                        FROM revisoes 
                        WHERE id_proposta_id = %s::uuid AND revisao = %s;
                    """, (str(id_proposta), numero_revisao))
                    
                    existing_revision = cur.fetchone()
                    revisao_id = dados.get('revisao_id')
                    
                    print(f"Revisão existente: {existing_revision}, ID: {revisao_id}")

                    if existing_revision or revisao_id:
                        print("Atualizando revisão existente")
                        result = RevisionService._atualizar_revisao(
                            cur,
                            dados,
                            valor_total,
                            numero_revisao,
                            word_path,
                            pdf_path,
                            revisao_id or str(existing_revision[0])
                        )
                    else:
                        print("Criando nova revisão")
                        result = RevisionService._inserir_revisao(
                            cur=cur,
                            dados=dados,
                            id_proposta=str(id_proposta),
                            valor=valor_total,
                            numero_revisao=numero_revisao,
                            word_path=word_path,
                            pdf_path=pdf_path
                        )

                    print("Resultado da operação:", result)
                    conn.commit()

                    if result:
                        import streamlit as st
                        st.success('Operação realizada com sucesso!')
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button('Voltar para o Django',key='voltar_django_salvar'):
                                st.components.v1.html(
                                    """
                                    <script>
                                        if (window.opener) {
                                            window.opener.postMessage('revisao_salva', '*');
                                            window.close();
                                        }
                                    </script>
                                    """,
                                    height=0
                                )
                        with col2:
                            if st.button('Continuar Editando',key='continuar_editando_salvar'):
                                st.rerun()

                    return bool(result)

            except Exception as e:
                print(f"Erro na operação do banco: {str(e)}")
                raise

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro detalhado: {str(e)}")
            raise Exception(f"Erro ao salvar revisão: {str(e)}")
        finally:
            if conn:
                conn.close()

    @staticmethod
    def _atualizar_revisao(cur, dados: Dict, valor: float, numero_revisao: int, 
                        word_path: str, pdf_path: str, revisao_id: str) -> Optional[str]:
        """Atualiza uma revisão existente"""
        try:
            print("Iniciando atualização da revisão...")
            
            # Primeiro verifica se é a última revisão
            cur.execute("""
                WITH rev_info AS (
                    SELECT r.revisao, r.id_proposta_id
                    FROM revisoes r
                    WHERE r.id_revisao = %s
                )
                SELECT 
                    rev_info.id_proposta_id,
                    rev_info.revisao,
                    (SELECT MAX(revisao) FROM revisoes WHERE id_proposta_id = rev_info.id_proposta_id) as ultima_revisao
                FROM rev_info;
            """, (revisao_id,))
            
            proposta_info = cur.fetchone()
            if proposta_info:
                id_proposta, revisao_atual, ultima_revisao = proposta_info
                
                # Se for a última revisão, atualiza o valor da proposta
                if revisao_atual == ultima_revisao:
                    print(f"Atualizando valor da proposta para {valor}")
                    cur.execute("""
                        UPDATE propostas 
                        SET valor = %s, 
                            dt_modificacao = NOW()
                        WHERE id_proposta = %s
                        RETURNING id_proposta;
                    """, (valor, id_proposta))
                    proposta_result = cur.fetchone()
                    print(f"Proposta {proposta_result[0]} atualizada com valor {valor}")
            
            # Continua com a atualização da revisão
            print(f"Atualizando revisão {revisao_id}")
            cur.execute("""
                UPDATE revisoes 
                SET conteudo = %s::jsonb, 
                    valor = %s,
                    revisao = %s,
                    dt_revisao = NOW(),
                    comentario = 'Revisão Atualizada',
                    arquivo = %s,
                    arquivo_pdf = %s
                WHERE id_revisao = %s
                RETURNING id_revisao;
            """, (
                json.dumps(dados, default=lambda x: float(x) if isinstance(x, Decimal) else x),
                valor,
                numero_revisao,
                word_path,
                pdf_path,
                revisao_id
            ))
            
            result = cur.fetchone()
            if result:
                print(f"Revisão {result[0]} atualizada com sucesso")
                return str(result[0])
            return None

        except Exception as e:
            print(f"Erro ao atualizar revisão: {str(e)}")
            raise

    @staticmethod
    def _salvar_arquivos(bt: str, rev: int, files: Dict[str, BytesIO]) -> Tuple[str, str]:
        """
        Salva os arquivos Word e PDF no sistema de arquivos.
        
        Args:
            bt: Número BT da proposta
            rev: Número da revisão
            files: Dicionário contendo os arquivos
            
        Returns:
            Tuple[str, str]: Caminhos relativos dos arquivos Word e PDF
        """
        base_path = "media/propostas"
        os.makedirs(base_path, exist_ok=True)

        word_filename = f"proposta_{bt}_rev{rev}.docx"
        pdf_filename = f"proposta_{bt}_rev{rev}.pdf"
        
        word_path = f"propostas/{word_filename}"
        pdf_path = f"propostas/{pdf_filename}"

        full_word_path = os.path.join("media", word_path)
        full_pdf_path = os.path.join("media", pdf_path)

        if 'word' in files:
            with open(full_word_path, 'wb') as f:
                f.write(files['word'].getvalue())

        if 'pdf' in files:
            with open(full_pdf_path, 'wb') as f:
                f.write(files['pdf'].getvalue())

        return word_path, pdf_path
    
    @staticmethod
    def _inserir_revisao(cur, dados: Dict, id_proposta: str, valor: float, 
                        numero_revisao: int, word_path: str, pdf_path: str) -> Optional[str]:
        """
        Insere uma nova revisão e atualiza o valor da proposta
        
        Args:
            cur: Cursor do banco de dados
            dados: Dicionário contendo todos os dados da revisão (session_state)
            id_proposta: ID da proposta
            valor: Valor total
            numero_revisao: Número da revisão
            word_path: Caminho do arquivo Word
            pdf_path: Caminho do arquivo PDF
        """
        try:
            # Primeiro atualiza o valor da proposta
            cur.execute("""
                UPDATE propostas 
                SET valor = %s, 
                    dt_modificacao = NOW()
                WHERE id_proposta = %s
                RETURNING id_proposta;
            """, (valor, id_proposta))
            
            proposta_result = cur.fetchone()

            # Preparar os dados que precisam ser salvos
            dados_para_salvar = {
                'itens_configurados': dados.get('itens_configurados', []),
                'impostos': dados.get('impostos', {}),
                'dados_iniciais': dados.get('dados_iniciais', {}),
                'configuracoes_itens': dados.get('configuracoes_itens', {})
            }

            # Converter para JSON com tratamento para Decimal
            dados_json = json.dumps(dados_para_salvar, default=lambda x: float(x) if isinstance(x, Decimal) else x)

            # Define o comentário baseado no número da revisão
            comentario = 'Revisão Inicial' if numero_revisao == 0 else dados.get('dados_iniciais', {}).get('comentario', '')

            cur.execute("""
                INSERT INTO revisoes (
                    id_revisao, 
                    id_proposta_id, 
                    valor, 
                    conteudo, 
                    revisao,
                    dt_revisao,
                    comentario,
                    arquivo,
                    arquivo_pdf
                )
                VALUES (
                    gen_random_uuid(), 
                    %s::uuid, 
                    %s, 
                    %s,
                    %s,
                    NOW(),
                    %s,
                    %s,
                    %s
                )
                RETURNING id_revisao::text;
            """, (
                id_proposta,
                valor,
                dados_json,
                numero_revisao,
                comentario,
                word_path,
                pdf_path
            ))
            
            result = cur.fetchone()
            return str(result[0]) if result else None

        except Exception as e:
            print(f"Erro ao inserir revisão: {str(e)}")
            raise