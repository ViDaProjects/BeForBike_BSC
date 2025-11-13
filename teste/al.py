import json
import random
import time

# --- Configurações ---
NUM_LINES = 3000
OUTPUT_FILENAME = "race.json"
RIDE_ID_TO_INCLUDE = 80 # ID fixo para incluir no JSON gerado

# Coordenadas base (Curitiba)
BASE_LAT = -25.4296
BASE_LON = -49.2675

# --- Geração dos Dados ---
print(f"Gerando {NUM_LINES} linhas de dados JSON (com ride_id={RIDE_ID_TO_INCLUDE}) para {OUTPUT_FILENAME}...")
lista = []
try:
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        for i in range(NUM_LINES):
            # Simula dados
            power = round(random.uniform(50.0, 400.0), 1)
            latitude = round(BASE_LAT + random.uniform(-0.01, 0.01), 6)
            longitude = round(BASE_LON + random.uniform(-0.01, 0.01), 6)
            velocity = round(random.uniform(0.0, 50.0), 1)

            # Cria o dicionário
            data_point = {
                "ride_id": RIDE_ID_TO_INCLUDE, # <-- ADICIONADO
                "power": power,
                "latitude": latitude,
                "longitude": longitude,
                "velocity": velocity,
                "power2": power,
                "latitude2": latitude,
                "longitude2": longitude,
                "velocity2": velocity,
                "power3": power,
                "latitude3": latitude,
                "longitude3": longitude,
                "velocity3": velocity,
                "power3": power,
                "latitude3": latitude,
                "longitude3": longitude,
                "velocity3": velocity

            }

            # Adiciona altitude opcionalmente
            if random.random() < 0.8:
                 data_point["altitude"] = round(random.uniform(850.0, 950.0), 1)

            # Converte para JSON e escreve no arquivo
            json_data = json.dumps(data_point)
            lista.append(json_data)

            # Progresso (opcional)
            if (i + 1) % 100 == 0:
                print(f"  {i + 1}/{NUM_LINES} linhas geradas...")
        
        #f.write(lista)
        json.dump(lista, f)
    

    print(f"\nArquivo '{OUTPUT_FILENAME}' gerado com sucesso!")

except Exception as e:
    print(f"\nErro ao gerar o arquivo: {e}")
