import os
import json
import requests
from datetime import datetime

# Configuração dos diretórios e URLs
CONTENTS_DIR = "contents"
INDEX_FILE = "index.json"
BASE_URL = "https://zenitheesc.github.io/launches-data/contents/"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS = {"User-Agent": "launches-data-bot"}

def get_city(lat, lon):
    """Obtém a cidade a partir das coordenadas usando a API do Nominatim."""
    if lat is None or lon is None:
        return "Desconhecido"
    
    try:
        response = requests.get(NOMINATIM_URL, params={"lat": lat, "lon": lon, "format": "json"}, headers=HEADERS)
        response.raise_for_status()
        return response.json().get("address", {}).get("city", "Desconhecido")
    except requests.RequestException as e:
        print(f"Erro ao buscar cidade para {lat}, {lon}: {e}")
        return "Desconhecido"

def process_json(filepath):
    """Lê um arquivo JSON e retorna informações relevantes do lançamento."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            return None

        first, last = data[0], data[-1]
        max_altitude = max((entry.get("alt", 0) for entry in data), default=0)

        return {
            "launch_city": get_city(first.get("lat"), first.get("lon")),
            "landing_city": get_city(last.get("lat"), last.get("lon")),
            "max_altitude": max_altitude,
            "launch_datetime": first.get("datetime", "Desconhecido")
        }
    except (json.JSONDecodeError, OSError) as e:
        print(f"Erro ao processar {filepath}: {e}")
        return None

def load_existing_index():
    """Carrega o index.json existente."""
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Erro ao carregar {INDEX_FILE}: {e}")
    return []

def generate_index():
    """Gera ou atualiza o index.json com novos arquivos JSON processados."""
    if not os.path.isdir(CONTENTS_DIR):
        print(f"Diretório '{CONTENTS_DIR}' não encontrado.")
        return

    existing_index = load_existing_index()
    processed_files = {entry["name"] for entry in existing_index}

    new_entries = []

    for file in filter(lambda f: f.endswith(".json") and f not in processed_files, os.listdir(CONTENTS_DIR)):
        print(f"Processando: {file}")
        metadata = process_json(os.path.join(CONTENTS_DIR, file))
        if metadata:
            new_entries.append({
                "name": file,
                "download_url": BASE_URL + file,
                **metadata
            })

    if new_entries:
        try:
            new_entries.sort(key=lambda x: datetime.strptime(x["launch_datetime"], "%Y-%m-%dT%H:%M:%S.%fZ"), reverse=True)
        except ValueError:
            print("Erro ao ordenar os lançamentos por data.")

        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_index + new_entries, f, indent=4, ensure_ascii=False)

        print(f"Index atualizado com {len(new_entries)} novos arquivos.")
    else:
        print("Nenhum novo arquivo encontrado. Index.json não foi modificado.")

if __name__ == "__main__":
    generate_index()
