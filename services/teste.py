import json

class PotenciaTransformadoresTeste:
    def __init__(self):
        # Configuração mínima para funcionar sem depender de streamlit ou configuração de logger
        self.logger = self.MockLogger()
    
    class MockLogger:
        """Mock logger para testes que imprime no console"""
        def info(self, msg):
            print(f"[INFO] {msg}")
        
        def warning(self, msg):
            print(f"[WARNING] {msg}")
            
        def error(self, msg):
            print(f"[ERROR] {msg}")
    
    def calcular_potencia_bt(self, itens_configurados_bt):
        """Calcula a potência total dos transformadores BT multiplicando pela quantidade"""
        soma = 0
        if itens_configurados_bt and isinstance(itens_configurados_bt, list):
            for item in itens_configurados_bt:
                try:
                    if isinstance(item, dict) and "potencia_numerica" in item and "quantidade" in item:
                        potencia = float(item["potencia_numerica"])
                        quantidade = int(item["quantidade"])
                        soma += potencia * quantidade  # Multiplicação pela quantidade
                        self.logger.info(f"Bola azul Potência BT: {potencia}, Quantidade: {quantidade}, Soma: {soma}")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Erro ao converter potência BT: {e}")
        return soma

    def calcular_potencia_mt(self, itens_configurados_mt):
        """Calcula a potência total dos transformadores MT multiplicando pela quantidade"""
        soma = 0
        if itens_configurados_mt and isinstance(itens_configurados_mt, list):
            for item in itens_configurados_mt:
                try:
                    if isinstance(item, dict) and "Potência" in item and "quantidade" in item:
                        potencia_str = ''.join(c for c in str(item["Potência"]) if c.isdigit() or c == '.')
                        potencia = float(potencia_str)
                        quantidade = int(item["quantidade"])
                        soma += potencia * quantidade  # Multiplicação pela quantidade
                        self.logger.info(f"Bola azul Potência MT: {potencia}, Quantidade: {quantidade}, Soma: {soma}")
                except (ValueError, TypeError, AttributeError) as e:
                    self.logger.warning(f"Erro ao converter potência MT: {e}")
        return soma

    def somar_potencias_transformadores(self, itens_configurados_bt, itens_configurados_mt, tipo='ambos'):
        """
        Calcula a potência total de acordo com o tipo especificado
        
        Parâmetros:
        tipo (str): 'bt', 'mt' ou 'ambos' (padrão)
        """
        soma_total = 0
        
        print(f"\n[TESTE] Somando potências - Tipo: {tipo}")
        
        if tipo in ('bt', 'ambos'):
            potencia_bt = self.calcular_potencia_bt(itens_configurados_bt)
            print(f"[TESTE] Potência BT: {potencia_bt}")
            soma_total += potencia_bt
            
        if tipo in ('mt', 'ambos'):
            potencia_mt = self.calcular_potencia_mt(itens_configurados_mt)
            print(f"[TESTE] Potência MT: {potencia_mt}")
            soma_total += potencia_mt

        try:
            soma_mva = soma_total / 1000
            resultado = f"{soma_mva:,.2f}".replace(".", ",").replace(",", ".", 1) + " MVA"
            print(f"[TESTE] Resultado final: {resultado}")
            return resultado
        except Exception as e:
            self.logger.error(f"Erro ao formatar potência: {e}")
            return "0,00 MVA"


# Dados de teste
dados_teste_bt = [
    {"potencia_numerica": 300, "quantidade": 2},
    {"potencia_numerica": 500, "quantidade": 1},
    {"potencia_numerica": 100, "quantidade": 3}
]

dados_teste_mt = [
    {"Potência": "1000 kVA", "quantidade": 2},
    {"Potência": "750 kVA", "quantidade": 1},
    {"Potência": "500 kVA", "quantidade": 3}
]

# Teste das funções
def executar_testes():
    print("=== INÍCIO DOS TESTES ===")
    teste = PotenciaTransformadoresTeste()
    
    print("\n=== TESTE 1: Calcular Potência BT ===")
    potencia_bt = teste.calcular_potencia_bt(dados_teste_bt)
    print(f"Potência BT total: {potencia_bt}")
    
    print("\n=== TESTE 2: Calcular Potência MT ===")
    potencia_mt = teste.calcular_potencia_mt(dados_teste_mt)
    print(f"Potência MT total: {potencia_mt}")
    
    print("\n=== TESTE 3: Somar Potências - Apenas BT ===")
    resultado_bt = teste.somar_potencias_transformadores(dados_teste_bt, [], tipo='bt')
    print(f"Resultado final BT: {resultado_bt}")
    
    print("\n=== TESTE 4: Somar Potências - Apenas MT ===")
    resultado_mt = teste.somar_potencias_transformadores([], dados_teste_mt, tipo='mt')
    print(f"Resultado final MT: {resultado_mt}")
    
    print("\n=== TESTE 5: Somar Potências - Ambos ===")
    resultado_ambos = teste.somar_potencias_transformadores(dados_teste_bt, dados_teste_mt, tipo='ambos')
    print(f"Resultado final AMBOS: {resultado_ambos}")
    
    print("\n=== FIM DOS TESTES ===")

if __name__ == "__main__":
    executar_testes()