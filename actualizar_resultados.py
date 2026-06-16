import requests

print("ESTE ES EL SCRIPT NUEVO ESPN")

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

try:
r = requests.get(URL, timeout=30)

```
print("=" * 60)
print("STATUS:", r.status_code)
print("=" * 60)

data = r.json()

print("Claves principales:")
print(list(data.keys()))

print("\nCantidad de eventos:")
print(len(data.get("events", [])))

print("\nPrimeros partidos encontrados:")
print("-" * 60)

for event in data.get("events", [])[:10]:
    print("Nombre:", event.get("name"))

    competitions = event.get("competitions", [])

    if competitions:
        comp = competitions[0]

        competitors = comp.get("competitors", [])

        if len(competitors) >= 2:
            home = competitors[0]
            away = competitors[1]

            print(
                f"{home['team']['displayName']} "
                f"{home.get('score', '?')} - "
                f"{away.get('score', '?')} "
                f"{away['team']['displayName']}"
            )

    print("-" * 60)
```

except Exception as e:
print("ERROR:")
print(e)
