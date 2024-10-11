
# **Proposta Automatizada de Média Tensão** 🏗️⚡

Este projeto foi desenvolvido pela **Tehokas Soluções** para uma empresa do ramo de transformadores. O objetivo é fornecer uma solução automatizada para a criação de propostas comerciais de transformadores de média tensão, permitindo uma configuração personalizada dos itens, cálculos precisos de preços e geração automática de documentos profissionais. A plataforma visa otimizar o tempo e garantir precisão nas informações fornecidas aos clientes.

## **Objetivo do Projeto** 🎯

A solução busca automatizar o processo de criação de propostas comerciais, eliminando a complexidade manual e o risco de erros. Com esta ferramenta, a equipe de vendas pode configurar especificações técnicas dos produtos e calcular preços de forma rápida e confiável. Além disso, a geração de documentos é feita automaticamente, com layout profissional e informações precisas.

## **Funcionalidades Principais** 🚀

### 1. **Configuração de Itens Técnicos** 🛠️
O sistema permite configurar parâmetros técnicos para cada transformador, incluindo:
- Potência nominal
- Tensão primária e secundária
- Derivações
- Classe de isolamento
- Grau de proteção (IP)
- Fator de perdas

### 2. **Cálculo de Preços** 💰
O sistema realiza cálculos automáticos com base nos dados inseridos, incluindo:
- Preço unitário do transformador
- Impostos (ICMS, IPI, Pis/Cofins)
- Custos adicionais, como margem de lucro, comissão, e frete
- Cálculo total da proposta comercial

### 3. **Geração de Documentos de Proposta** 📄
A plataforma gera automaticamente uma proposta em formato profissional, pronta para ser enviada ao cliente, incluindo:
- Resumo técnico dos itens configurados
- Quadro de preços detalhado
- Escopo do fornecimento
- Observações adicionais

### 4. **Integração com Banco de Dados** 🔗
O sistema permite integração com um banco de dados personalizado, onde todas as propostas podem ser armazenadas e gerenciadas de maneira centralizada. A estrutura do banco de dados é flexível e pode ser configurada de acordo com as necessidades da empresa.

## **Configuração do Banco de Dados** 🗄️

Para utilizar a funcionalidade de banco de dados no projeto, será necessário configurar um banco de dados Postgres ou outro de sua preferência. A tabela principal utilizada no projeto é chamada de **`custos_media_tensao`** e possui a seguinte estrutura:

### **Estrutura da Tabela `custos_media_tensao`**:

| Coluna              | Tipo de Dados  | Descrição                                         |
|---------------------|----------------|---------------------------------------------------|
| `p_caixa`           | `FLOAT`        | Peso da caixa (transformador)                     |
| `p_trafo`           | `FLOAT`        | Peso do transformador                             |
| `potencia`          | `FLOAT`        | Potência nominal do transformador                 |
| `perdas`            | `VARCHAR`      | Tipo de perdas (ex.: 1,2%, 1,0%, etc.)            |
| `classe`            | `VARCHAR`      | Classe de tensão                                  |
| `valor_ip_baixo`    | `FLOAT`        | Valor de IP (Grau de proteção) baixo              |
| `valor_ip_alto`     | `FLOAT`        | Valor de IP (Grau de proteção) alto               |
| `custo`             | `FLOAT`        | Custo calculado do transformador                  |

### **Passos para Configuração do Banco de Dados**:

1. **Criar o Banco de Dados**:
   - Instale e configure o PostgreSQL (ou outro banco de dados de sua escolha).
   - Crie um banco de dados novo:
     ```sql
     CREATE DATABASE proposta_mediatensao;
     ```

2. **Criar a Tabela `custos_media_tensao`**:
   - Execute o script SQL abaixo para criar a tabela:
     ```sql
     CREATE TABLE custos_media_tensao (
       p_caixa FLOAT,
       p_trafo FLOAT,
       potencia FLOAT,
       perdas VARCHAR(50),
       classe VARCHAR(50),
       valor_ip_baixo FLOAT,
       valor_ip_alto FLOAT,
       custo FLOAT
     );
     ```

3. **Inserir Dados na Tabela**:
   - Insira os dados da tabela manualmente ou crie um arquivo `.csv` para carregar os dados:
     ```sql
     INSERT INTO custos_media_tensao (p_caixa, p_trafo, potencia, perdas, classe, valor_ip_baixo, valor_ip_alto, custo)
     VALUES (120, 450, 1500, '1,2%', '15kV', 500, 800, 20000);
     ```

4. **Configurar a Conexão no Código**:
   - Atualize o arquivo de configuração do projeto para incluir os detalhes da conexão ao banco de dados:
     ```python
     DATABASE_CONFIG = {
         'dbname': 'proposta_mediatensao',
         'user': 'seu_usuario',
         'password': 'sua_senha',
         'host': 'localhost',
         'port': 5432
     }
     ```

## **Benefícios para o Cliente** 💼

1. **Automação Completa**: O processo de criação de propostas é completamente automatizado, economizando tempo e evitando erros.
2. **Redução de Custos**: Cálculos precisos e automáticos garantem que o orçamento seja otimizado.
3. **Armazenamento Centralizado**: Propostas geradas e armazenadas no banco de dados, facilitando o acesso e gerenciamento centralizado.
4. **Flexibilidade**: O sistema permite ajustes e personalizações para diferentes clientes e requisitos técnicos.

## **Como Executar o Projeto** 🏃‍♂️

1. Clone o repositório:
   ```bash
   git clone https://github.com/tehokas/proposta-automatica-transformadores.git
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure o banco de dados e insira os dados conforme instruções acima.

4. Execute a aplicação:
   ```bash
   streamlit run app.py
   ```

5. Acesse o sistema via browser para gerar propostas automatizadas.

## **Segurança e Acesso Restrito** 🔐

O sistema oferece a opção de restringir o acesso apenas aos membros da equipe, utilizando métodos como autenticação via **Azure Active Directory**, **Google OAuth**, ou senhas personalizadas, garantindo que apenas pessoas autorizadas tenham acesso às funcionalidades da plataforma.

## **Contato** 📞

Para dúvidas e suporte técnico, entre em contato com a **Tehokas Soluções**:

- **Email**: contato@tehokas.com.br
- **Telefone**: +55 (31) 98872-5513

---

### **Tehokas Soluções** - Inovação com eficiência ⚙️

