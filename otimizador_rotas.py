import pandas as pd
import heapq
import math
from sklearn.cluster import KMeans

# --- PARTE 1: IMPLEMENTAÇÃO DO A* (A-ESTRELA) ---

class Roteirizador:
    def __init__(self, locais_path, mapa_path):
        self.locais_coords = self._carregar_locais(locais_path)
        self.grafo = self._carregar_grafo(mapa_path)

    def _carregar_locais(self, locais_path):
        """Carrega as coordenadas (x,y) dos locais."""
        df_locais = pd.read_csv(locais_path)
        locais = {}
        for _, row in df_locais.iterrows():
            locais[row['Nome']] = (row['x'], row['y'])
        return locais

    def _carregar_grafo(self, mapa_path):
        """Carrega o grafo (mapa) a partir do CSV de arestas."""
        df_mapa = pd.read_csv(mapa_path)
        grafo = {}
        for _, row in df_mapa.iterrows():
            origem, destino, peso = row['Origem'], row['Destino'], row['Peso']
            if origem not in grafo:
                grafo[origem] = {}
            if destino not in grafo:
                grafo[destino] = {}
            grafo[origem][destino] = peso
            grafo[destino][origem] = peso # Assumindo ruas de mão dupla
        return grafo

    def _heuristica(self, no_atual, no_objetivo):
        """Calcula a distância Euclidiana (linha reta) como heurística."""
        x1, y1 = self.locais_coords[no_atual]
        x2, y2 = self.locais_coords[no_objetivo]
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    def calcular_rota_a_estrela(self, inicio, fim):
        """Encontra o caminho mais curto usando A* (A-Estrela)."""
        fila_prioridade = [(0 + self._heuristica(inicio, fim), 0, inicio, [inicio])]
        custo_g_conhecido = {inicio: 0}
        
        while fila_prioridade:
            f_score, g_score, no_atual, caminho = heapq.heappop(fila_prioridade)
            
            if no_atual == fim:
                return caminho, g_score # Retorna caminho e custo
                
            for vizinho, peso in self.grafo.get(no_atual, {}).items():
                novo_g_score = g_score + peso
                
                if vizinho not in custo_g_conhecido or novo_g_score < custo_g_conhecido[vizinho]:
                    custo_g_conhecido[vizinho] = novo_g_score
                    h_score = self._heuristica(vizinho, fim)
                    novo_f_score = novo_g_score + h_score
                    heapq.heappush(fila_prioridade, 
                                   (novo_f_score, novo_g_score, vizinho, caminho + [vizinho]))
        
        return None, 0 # Não há caminho

# --- PARTE 2: IMPLEMENTAÇÃO DO K-MEANS (CLUSTERING) ---

def agrupar_pedidos_kmeans(pedidos_df, locais_coords, num_entregadores):
    """
    Agrupa pedidos em 'zonas' usando K-Means.
    """
    # Pega as coordenadas (x,y) de cada local de pedido
    dados_pedidos = []
    for local in pedidos_df['Local_Entrega']:
        dados_pedidos.append(locais_coords[local])
    
    if not dados_pedidos:
        return []

    # Executa o K-Means
    kmeans = KMeans(n_clusters=num_entregadores, random_state=42, n_init=10)
    pedidos_df['Cluster'] = kmeans.fit_predict(dados_pedidos)
    
    # Organiza os pedidos por cluster
    zonas = []
    for i in range(num_entregadores):
        pedidos_da_zona = pedidos_df[pedidos_df['Cluster'] == i]['Local_Entrega'].tolist()
        if pedidos_da_zona:
            zonas.append(pedidos_da_zona)
            
    return zonas

# --- PARTE 3: EXECUÇÃO DO PROJETO "ROTA INTELIGENTE" ---

def main():
    print("🚀 Iniciando Otimizador de Rotas 'Sabor Express'...")
    
    # Configurações
    PONTO_PARTIDA = 'SaborExpress_Base'
    NUM_ENTREGADORES = 3 # Defina quantos entregadores (clusters)
    
    # Carrega dados
    try:
        roteirizador = Roteirizador('locais.csv', 'mapa.csv')
        pedidos_pendentes_df = pd.read_csv('pedidos.csv')
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado. Verifique se {e.filename} está na pasta.")
        return

    print(f"Total de {len(pedidos_pendentes_df)} pedidos pendentes.")
    print(f"Dividindo em {NUM_ENTREGADORES} zonas de entrega...")

    # Passo 1: Agrupar pedidos com K-Means [cite: 18, 19]
    locais_dos_pedidos = roteirizador.locais_coords
    zonas_de_entrega = agrupar_pedidos_kmeans(pedidos_pendentes_df, 
                                            locais_dos_pedidos, 
                                            NUM_ENTREGADORES)
    
    print("\n--- Zonas de Entrega (Clusters) ---")
    for i, zona in enumerate(zonas_de_entrega):
        print(f"Zona/Entregador {i+1}: {', '.join(zona)}")

    print("\n--- Calculando Rotas Otimizadas (A*) ---")
    
    # Passo 2: Calcular a rota para cada zona/entregador [cite: 13, 19]
    for i, zona in enumerate(zonas_de_entrega):
        print(f"\n🚚 Rota do Entregador {i+1}:")
        
        local_atual = PONTO_PARTIDA
        rota_completa_entregador = [PONTO_PARTIDA]
        distancia_total_entregador = 0
        
        # Roteiriza para cada pedido na zona
        # (Nota: Isso é uma heurística simples, não o "Problema do Caixeiro Viajante" completo)
        for pedido_local in zona:
            rota_trecho, custo_trecho = roteirizador.calcular_rota_a_estrela(local_atual, pedido_local)
            
            if rota_trecho:
                # Adiciona o trecho, removendo o primeiro nó (que é o local atual)
                rota_completa_entregador.extend(rota_trecho[1:])
                distancia_total_entregador += custo_trecho
                local_atual = pedido_local # Atualiza o local para o próximo cálculo
            else:
                print(f"  [ALERTA] Não foi possível encontrar rota de {local_atual} para {pedido_local}")

        # Opcional: Adicionar rota de volta à base
        rota_volta, custo_volta = roteirizador.calcular_rota_a_estrela(local_atual, PONTO_PARTIDA)
        if rota_volta:
            rota_completa_entregador.extend(rota_volta[1:])
            distancia_total_entregador += custo_volta
        
        # Imprime resultados para este entregador
        print(f"  Distância Total: {distancia_total_entregador:.2f} km")
        print(f"  Sequência de Paradas: {' -> '.join(rota_completa_entregador)}")

# Ponto de entrada do script
if __name__ == "__main__":
    main()