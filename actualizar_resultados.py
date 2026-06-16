import requests
import json

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

r = requests.get(URL, timeout=30)

print("STATUS HTTP:", r.status_code)

data = r.json()

print("Cantidad de eventos:", len(data.get("events", [])))

if len(data.get("events", [])) == 0:
    print("No se encontraron eventos")
    quit()

evento = data["events"][0]

print("\n" + "=" * 80)
print("PRIMER EVENTO COMPLETO")
print("=" * 80)

print(json.dumps(evento, indent=2, ensure_ascii=False))
