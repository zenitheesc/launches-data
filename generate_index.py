import os
import json
import requests

# Configuração dos diretórios e URLs
CONTENTS_DIR = "contents"
INDEX_FILE = "index.json"  # O index.json será gerado na raiz
BASE_URL = "https://zenitheesc.github.io/launches-data/contents/"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

def get_city_from_coordinates(lat, lon):
    """Obtém a cidade a partir das coordenadas usando a API do Nominatim (OpenStreetMap)."""
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": "launches-data-bot"})
        if response.status_code == 200:
            data = response.json()
            return data.get("address", {}).get("city", "Desconhecido")
    except Exception as e:
        print(f"Erro ao buscar cidade para {lat}, {lon}: {e}")
    return "Desconhecido"

def process_json_file(filepath):
    """Lê o arquivo JSON e retorna a cidade de lançamento e a altitude máxima."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            return None

        # Pega a primeira coordenada para identificar a cidade
        first_entry = data[0]
        lat, lon = first_entry.get("lat"), first_entry.get("lon")

        # Obtém a altitude máxima
        max_altitude = max(entry.get("alt", 0) for entry in data)

        # Obtém a cidade
        city = get_city_from_coordinates(lat, lon) if lat and lon else "Desconhecido"

        return {
            "launch_city": city,
            "max_altitude": max_altitude
        }
    except Exception as e:
        print(f"Erro ao processar {filepath}: {e}")
        return None

def load_existing_index():
    """Carrega o index.json existente para evitar reprocessamento."""
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {INDEX_FILE}: {e}")
    return []

def generate_index():
    """Gera um arquivo index.json apenas com novos arquivos."""
    if not os.path.exists(CONTENTS_DIR):
        print(f"Diretório '{CONTENTS_DIR}' não encontrado.")
        return

    # Carrega o índice existente
    existing_index = load_existing_index()
    processed_files = {entry["name"] for entry in existing_index}

    new_entries = []

    for file in os.listdir(CONTENTS_DIR):
        if file.endswith(".json") and file not in processed_files:
            file_path = os.path.join(CONTENTS_DIR, file)
            metadata = process_json_file(file_path)
            if metadata:
                new_entries.append({
                    "name": file,
                    "download_url": BASE_URL + file,
                    "launch_city": metadata["launch_city"],
                    "max_altitude": metadata["max_altitude"]
                })

    # Só atualiza o index.json se houver novos arquivos
    if new_entries:
        updated_index = existing_index + new_entries
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_index, f, indent=4, ensure_ascii=False)

        print(f"Index atualizado com {len(new_entries)} novos arquivos.")
    else:
        print("Nenhum novo arquivo encontrado. Index.json não foi modificado.")

if __name__ == "__main__":
    generate_index()
