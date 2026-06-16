"""
Actualiza resultados.xlsx con los resultados del Mundial usando API-Football.

Columnas del Excel (sin encabezados, fila 1 = primer partido):
  A: pais 1
  B: goles pais 1
  C: goles pais 2
  D: pais 2
  H: 1 si el partido terminó (FT), vacío si no

Requiere variable de entorno API_FOOTBALL_KEY (API-Football / api-sports.io).
"""

import os
import sys
import time
import unicodedata
import requests
import openpyxl

EXCEL_PATH = "resultados.xlsx"
API_KEY = os.environ.get("API_FOOTBALL_KEY")
LEAGUE_ID = 1          # World Cup en API-Football
SEASON = 2026          # Temporada del Mundial 2026

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}


def normalizar(texto):
    """Quita tildes, pasa a minúsculas y recorta espacios para comparar nombres."""
    if texto is None:
        return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


# Traducciones español -> nombre que usa API-Football en inglés.
# Agrega/ajusta aquí si algún equipo no calza.
TRADUCCIONES = {
    "alemania": "germany",
    "argentina": "argentina",
    "arabia saudita": "saudi arabia",
    "australia": "australia",
    "belgica": "belgium",
    "bosnia y herzegovina": "bosnia and herzegovina",
    "brasil": "brazil",
    "cabo verde": "cape verde",
    "canada": "canada",
    "colombia": "colombia",
    "corea del sur": "south korea",
    "costa de marfil": "ivory coast",
    "croacia": "croatia",
    "curacao": "curacao",
    "ecuador": "ecuador",
    "egipto": "egypt",
    "escocia": "scotland",
    "espana": "spain",
    "estados unidos": "usa",
    "francia": "france",
    "ghana": "ghana",
    "haiti": "haiti",
    "inglaterra": "england",
    "irak": "iraq",
    "iran": "iran",
    "italia": "italy",
    "japon": "japan",
    "jordania": "jordan",
    "marruecos": "morocco",
    "mexico": "mexico",
    "nueva zelanda": "new zealand",
    "noruega": "norway",
    "panama": "panama",
    "paraguay": "paraguay",
    "paises bajos": "netherlands",
    "polonia": "poland",
    "portugal": "portugal",
    "qatar": "qatar",
    "republica checa": "czech republic",
    "senegal": "senegal",
    "sudafrica": "south africa",
    "suecia": "sweden",
    "suiza": "switzerland",
    "tunisia": "tunisia",
    "turquia": "turkey",
    "uruguay": "uruguay",
    "uzbekistan": "uzbekistan",
}


def nombre_api(nombre_excel):
    key = normalizar(nombre_excel)
    return TRADUCCIONES.get(key, key)


def obtener_partidos_api():
    """Trae todos los partidos del Mundial desde API-Football."""
    url = f"{BASE_URL}/fixtures"
    params = {"league": LEAGUE_ID, "season": SEASON}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print("Respuesta API:")
    print(data)

    if data.get("errors"):
        print("API devolvió errores:", data["errors"], file=sys.stderr)

    partidos = []
    for item in data.get("response", []):
        home = item["teams"]["home"]["name"]
        away = item["teams"]["away"]["name"]
        status = item["fixture"]["status"]["short"]  # FT, NS, 1H, etc.
        goals_home = item["goals"]["home"]
        goals_away = item["goals"]["away"]

        partidos.append({
            "home": normalizar(home),
            "away": normalizar(away),
            "finalizado": status == "FT",
            "goles_home": goals_home,
            "goles_away": goals_away,
        })
    return partidos


def actualizar_excel(partidos):
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active

    # Índice rápido por par de equipos (en ambos sentidos)
    indice = {}
    for p in partidos:
        indice[(p["home"], p["away"])] = p
        indice[(p["away"], p["home"])] = p

    actualizados = 0

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        celda_a = row[0]  # A
        celda_b = row[1]  # B
        celda_c = row[2]  # C
        celda_d = row[3]  # D
        celda_h = row[7]  # H

        if celda_a.value is None or celda_d.value is None:
            continue

        # Si ya está marcado como finalizado, no lo tocamos
        if celda_h.value == 1:
            continue

        pais1 = nombre_api(celda_a.value)
        pais2 = nombre_api(celda_d.value)

        partido = indice.get((pais1, pais2))
        if partido is None:
            continue

        if not partido["finalizado"]:
            continue

        if pais1 == partido["home"]:
            goles1, goles2 = partido["goles_home"], partido["goles_away"]
        else:
            goles1, goles2 = partido["goles_away"], partido["goles_home"]

        if goles1 is None or goles2 is None:
            continue

        celda_b.value = goles1
        celda_c.value = goles2
        celda_h.value = 1
        actualizados += 1
        print(f"Actualizado: {celda_a.value} {goles1} - {goles2} {celda_d.value}")

    if actualizados > 0:
        wb.save(EXCEL_PATH)
        print(f"{actualizados} partido(s) actualizado(s). Excel guardado.")
    else:
        print("Sin cambios: no hay partidos nuevos finalizados.")

    return actualizados


def main():
    if not API_KEY:
        print("ERROR: falta la variable de entorno API_FOOTBALL_KEY", file=sys.stderr)
        sys.exit(1)

    partidos = obtener_partidos_api()
    print(f"Partidos obtenidos desde la API: {len(partidos)}")
    actualizar_excel(partidos)


if __name__ == "__main__":
    main()
