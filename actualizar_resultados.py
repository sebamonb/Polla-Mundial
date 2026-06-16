import requests
from openpyxl import load_workbook

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

mapa = {
    "Francia": "France",
    "Brasil": "Brazil",
    "Alemania": "Germany",
    "Espana": "Spain",
    "Mexico": "Mexico",
    "Canada": "Canada",
    "Sudafrica": "South Africa",
    "Corea del Sur": "South Korea",
    "Republica Checa": "Czechia",
    "Bosnia y Herzegovina": "Bosnia and Herzegovina",
    "Estados Unidos": "United States",
    "Paraguay": "Paraguay",
    "Qatar": "Qatar",
    "Suiza": "Switzerland"
}

r = requests.get(URL)
data = r.json()

events = data["events"]

wb = load_workbook("resultados.xlsx")
ws = wb.active

for event in events:

    comp = event["competitions"][0]
    if not comp["status"]["type"]["completed"]:
        continue

    competitors = comp["competitors"]

    home = away = home_score = away_score = None

    for c in competitors:
        name = c["team"]["displayName"]
        score = c["score"]

        if c["homeAway"] == "home":
            home = name
            home_score = score
        else:
            away = name
            away_score = score

    for row in ws.iter_rows(min_row=1):

        excel_home = row[0].value
        excel_away = row[3].value
        flag = row[7].value

        if flag == 1:
            continue

        excel_home_en = mapa.get(excel_home, excel_home)
        excel_away_en = mapa.get(excel_away, excel_away)

        if excel_home_en == home and excel_away_en == away:
            row[1].value = home_score
            row[2].value = away_score
            row[7].value = 1

        elif excel_home_en == away and excel_away_en == home:
            row[1].value = away_score
            row[2].value = home_score
            row[7].value = 1

wb.save("resultados.xlsx")
