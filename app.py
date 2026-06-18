import glob
import os
import pandas as pd
import numpy as np
import streamlit as st

# ---- BANDERAS ----

codigos_iso = {
    "Canada": "ca", "Estados Unidos": "us", "Mexico": "mx",
    "Argentina": "ar", "Brasil": "br", "Colombia": "co",
    "Ecuador": "ec", "Paraguay": "py", "Uruguay": "uy",
    "Alemania": "de", "Austria": "at", "Belgica": "be",
    "Bosnia y Herzegovina": "ba", "Croacia": "hr", "Escocia": "gb-sct",
    "Espana": "es", "Francia": "fr", "Inglaterra": "gb-eng",
    "Noruega": "no", "Paises Bajos": "nl", "Portugal": "pt",
    "Republica Checa": "cz", "Suecia": "se", "Suiza": "ch",
    "Turquia": "tr", "Arabia Saudita": "sa", "Australia": "au",
    "Corea del Sur": "kr", "Iran": "ir", "Japon": "jp",
    "Jordania": "jo", "Qatar": "qa", "Uzbekistan": "uz",
    "Argelia": "dz", "Cabo Verde": "cv", "Costa de Marfil": "ci",
    "Egipto": "eg", "Ghana": "gh", "Marruecos": "ma",
    "RD Congo": "cd", "Senegal": "sn", "Sudafrica": "za",
    "Tunisia": "tn", "Curacao": "cw", "Haiti": "ht",
    "Iraq": "iq", "Jamaica": "jm", "Panama": "pa",
    "Nueva Zelanda": "nz",
}

def bandera_url(pais):
    codigo = codigos_iso.get(pais, "")
    if codigo:
        return f"https://flagcdn.com/w40/{codigo}.png"
    return None

# ---- FUNCIONES ----

def CALCULAR_PUNTOS(df_resultado, df_participante):
    df_participante = df_participante.reset_index(drop=True)
    df_resultado    = df_resultado.reset_index(drop=True)

    df_participante["E"] = np.where(df_participante["B"] > df_participante["C"], "L",
                            np.where(df_participante["B"] < df_participante["C"], "V", "E"))

    p_jugados = int(df_resultado["H"].count())

    if p_jugados == 0:
        df_participante["F"] = None
        return df_participante

    condiciones = [
        (df_resultado["B"][:p_jugados] == df_participante["B"][:p_jugados]) &
        (df_resultado["C"][:p_jugados] == df_participante["C"][:p_jugados]),
        (df_resultado["E"][:p_jugados] == df_participante["E"][:p_jugados])
    ]
    valores = [3, 1]
    df_participante["F"] = None
    df_participante.loc[:p_jugados - 1, "F"] = np.select(condiciones, valores, default=0)
    return df_participante


def TABLA_PUNTAJES(participantes):
    resultados = []
    for nombre, df_participante in participantes:
        total_puntos  = df_participante["F"].sum()
        total_exactos = (df_participante["F"] == 3).sum()
        resultados.append([nombre, total_puntos, total_exactos])
    df_tabla = pd.DataFrame(resultados, columns=["Nombre", "Puntos", "Exactos"])
    df_tabla = df_tabla.sort_values(by=["Puntos", "Exactos"], ascending=False)
    return df_tabla


def PREDICCIONES(participantes, total, df_resultado):
    tablas_fechas = []
    for i in range(total):
        # Equipo local y visitante vienen de df_resultado si la fila existe
        if i < len(df_resultado):
            equipo_local   = df_resultado.iloc[i]["A"]
            equipo_visita  = df_resultado.iloc[i]["D"]
        else:
            equipo_local  = "-"
            equipo_visita = "-"

        tabla_fecha = []
        for nombre, df_participante in participantes:
            if i < len(df_participante):
                prediccion_b = df_participante.iloc[i]["B"]
                prediccion_c = df_participante.iloc[i]["C"]
                puntos_fila  = df_participante.iloc[i]["F"]
            else:
                prediccion_b = "-"
                prediccion_c = "-"
                puntos_fila  = None
            tabla_fecha.append([nombre, prediccion_b, prediccion_c, puntos_fila])

        df_fecha        = pd.DataFrame(tabla_fecha, columns=["Nombre", "B", "C", "F"])
        df_fecha["A"]   = equipo_local
        df_fecha["D"]   = equipo_visita
        tablas_fechas.append(df_fecha)
    return tablas_fechas

# ---- CÓDIGO PRINCIPAL ----

df_resultado = pd.read_excel("resultados.xlsx", header=None,
                             names=["A","B","C","D","E","F","G","H"])
p_jugados = int(df_resultado["H"].count())
df_resultado["E"] = np.where(df_resultado["B"] > df_resultado["C"], "L",
                    np.where(df_resultado["B"] < df_resultado["C"], "V", "E"))

archivos = glob.glob("carpeta/*.xlsx")
participantes = []
for archivo in archivos:
    nombre         = os.path.splitext(os.path.basename(archivo))[0]
    df_participante = pd.read_excel(archivo, header=None,
                                    names=["A","B","C","D","E","F","G","H"])
    df_participante = CALCULAR_PUNTOS(df_resultado, df_participante)
    participantes.append([nombre, df_participante])

df_tabla      = TABLA_PUNTAJES(participantes)
tablas_fechas = PREDICCIONES(participantes, 78, df_resultado)

# ---- STREAMLIT ----


st.markdown("""
    <style>
    .stProgress { display: none; }
    div[data-testid="stStatusWidget"] { display: none; }
    </style>
""", unsafe_allow_html=True)


st.title("🏆 Polla Mundial")

pestaña1, pestaña2 = st.tabs(["Tabla General", "Predicciones por Fecha"])
########################################################################################################
with pestaña1:
    st.subheader("Clasificación General")
    st.write(f"Participantes cargados: {len(participantes)}")
    st.write(f"Filas en df_tabla: {len(df_tabla)}")

    MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉"}

    filas = ""
    for i, row in df_tabla.reset_index(drop=True).iterrows():
        if i < 3:
            estilo = "border-left: 4px solid #00C853; background-color: rgba(0, 200, 83, 0.08);"
        else:
            estilo = ""
        posicion = i + 1
        medalla = MEDALLAS.get(posicion, str(posicion))
        fila = "<tr style='{e}'><td>{m}</td><td>{n}</td><td>{p}</td><td>{x}</td></tr>".format(
            e=estilo, m=medalla, n=row['Nombre'], p=int(row['Puntos']), x=int(row['Exactos'])
        )
        filas += fila
    html = f"""
    <table style="width:100%; text-align:center; border-collapse:collapse;">
        <thead><tr>
            <th style="padding:8px;">#</th>
            <th style="padding:8px;">Nombre</th>
            <th style="padding:8px;">Puntos</th>
            <th style="padding:8px;">Exactos</th>
        </tr></thead>
        <tbody>{filas}</tbody>
    </table>
    <br>
    """
    st.markdown(html, unsafe_allow_html=True)
    ########################################################################################################################3

with pestaña2:
    st.subheader("Predicciones por Fecha")
    if "fecha" not in st.session_state:
        st.session_state.fecha = p_jugados if p_jugados > 0 else 1

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀") and st.session_state.fecha > 1:
            st.session_state.fecha -= 1
    with col2:
        st.markdown(f"### Partido {st.session_state.fecha}")
    with col3:
        if st.button("▶") and st.session_state.fecha < 78:
            st.session_state.fecha += 1

    df_fecha_actual = tablas_fechas[st.session_state.fecha - 1]

    # Encabezado del partido con banderas
    equipo_local  = df_fecha_actual.iloc[0]["A"]
    equipo_visita = df_fecha_actual.iloc[0]["D"]
    url_l = bandera_url(equipo_local)
    url_v = bandera_url(equipo_visita)

   # Obtener resultado real si el partido fue jugado
    if st.session_state.fecha <= p_jugados:
        gol_l = df_resultado.iloc[st.session_state.fecha - 1]["B"]
        gol_v = df_resultado.iloc[st.session_state.fecha - 1]["C"]
        marcador_texto = f"{int(gol_l)} - {int(gol_v)}"
    else:
        marcador_texto = "vs"

    c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 3, 1])
    with c1:
        if url_l:
            st.image(url_l, width=60)
    with c2:
        st.markdown(f"<h2 style='text-align:center'>{equipo_local}</h2>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<h2 style='text-align:center'>{marcador_texto}</h2>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<h2 style='text-align:center'>{equipo_visita}</h2>", unsafe_allow_html=True)
    with c5:
        if url_v:
            st.image(url_v, width=60)

    st.divider()
    # Tabla de predicciones de todos los participantes
    df_mostrar = df_fecha_actual[["Nombre", "B", "C", "F"]].rename(
        columns={"B": equipo_local, "C": equipo_visita, "F": "Puntos"}
    ).reset_index(drop=True)

    filas_pred = ""
    for _, row in df_mostrar.iterrows():
        puntos = int(row["Puntos"]) if pd.notna(row["Puntos"]) else "-"

        # Definir color de fondo solo para la celda de Puntos, solo si el partido fue jugado
        if puntos == 3:
            estilo_puntos = "background-color: rgba(0, 200, 83, 0.25);"
        elif puntos == 1:
            estilo_puntos = "background-color: rgba(255, 193, 7, 0.25);"
        elif puntos == 0:
            estilo_puntos = "background-color: rgba(244, 67, 54, 0.25);"
        else:
            estilo_puntos = ""  # partido no jugado, sin color

        filas_pred += f"<tr><td>{row['Nombre']}</td><td>{row[equipo_local]}</td><td>{row[equipo_visita]}</td><td style='{estilo_puntos}'>{puntos}</td></tr>"

    html_pred = f"""
    <table style="width:100%; text-align:center; border-collapse:collapse;">
        <thead><tr>
            <th style="padding:8px;">Nombre</th>
            <th style="padding:8px;">{equipo_local}</th>
            <th style="padding:8px;">{equipo_visita}</th>
            <th style="padding:8px;">Puntos</th>
        </tr></thead>
        <tbody>{filas_pred}</tbody>
    </table>
    <br>
    """
    st.markdown(html_pred, unsafe_allow_html=True)

