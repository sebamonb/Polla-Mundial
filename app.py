import glob
import os
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

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

def es_numero(valor):
    """
    True si 'valor' es una predicción numérica válida.
    False si es NaN, o texto tipo 'X' / '-' (sin predicción / partido futuro).
    """
    if pd.isna(valor):
        return False
    if isinstance(valor, str):
        if valor.strip().upper() in ("X", "-", ""):
            return False
        try:
            float(valor)
            return True
        except ValueError:
            return False
    return True


def CALCULAR_PUNTOS(df_resultado, df_participante):
    df_participante = df_participante.reset_index(drop=True)
    df_resultado    = df_resultado.reset_index(drop=True)

    # Marca por fila si la predicción del participante es numérica válida
    df_participante["valido"] = df_participante.apply(
        lambda row: es_numero(row["B"]) and es_numero(row["C"]), axis=1
    )

    def calcular_E(row):
        if not (es_numero(row["B"]) and es_numero(row["C"])):
            return None
        b, c = float(row["B"]), float(row["C"])
        if b > c:
            return "L"
        elif b < c:
            return "V"
        else:
            return "E"

    df_participante["E"] = df_participante.apply(calcular_E, axis=1)

    # Máscara de partidos con resultado real (H no nulo), sin asumir continuidad
    mask_jugados = df_resultado["H"].notna()
    indices_jugados = df_resultado.index[mask_jugados]

    df_participante["F"] = None

    if len(indices_jugados) == 0:
        return df_participante

    for i in indices_jugados:
        if i >= len(df_participante):
            continue

        res_b = df_resultado.iloc[i]["B"]
        res_c = df_resultado.iloc[i]["C"]
        res_e = df_resultado.iloc[i]["E"]

        # Si el resultado tiene NaN en goles, saltar
        if pd.isna(res_b) or pd.isna(res_c):
            continue

        # Si el participante no mandó una predicción numérica válida -> 0 puntos
        if not df_participante.iloc[i]["valido"]:
            df_participante.at[i, "F"] = 0
            continue

        pred_b = float(df_participante.iloc[i]["B"])
        pred_c = float(df_participante.iloc[i]["C"])
        pred_e = df_participante.iloc[i]["E"]

        if pred_b == res_b and pred_c == res_c:
            df_participante.at[i, "F"] = 3
        elif pred_e == res_e:
            df_participante.at[i, "F"] = 1
        else:
            df_participante.at[i, "F"] = 0

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
    for i in range(len(df_resultado)):
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
total_partidos = len(df_resultado)

# p_jugados se usa solo para UI (navegación inicial), NO para lógica de puntos
p_jugados = int(df_resultado["H"].count())

df_resultado["E"] = np.where(df_resultado["B"] > df_resultado["C"], "L",
                    np.where(df_resultado["B"] < df_resultado["C"], "V", "E"))

archivos = glob.glob("carpeta/*.xlsx")
participantes = []
for archivo in archivos:
    nombre          = os.path.splitext(os.path.basename(archivo))[0]
    df_participante = pd.read_excel(archivo, header=None,
                                    names=["A","B","C","D","E","F","G","H"])
    df_participante = CALCULAR_PUNTOS(df_resultado, df_participante)
    participantes.append([nombre, df_participante])

df_tabla      = TABLA_PUNTAJES(participantes)
tablas_fechas = PREDICCIONES(participantes, total_partidos, df_resultado)

# ---- STREAMLIT ----

st.markdown("""
    <style>
    .stProgress { display: none; }
    div[data-testid="stStatusWidget"] { display: none; }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 Polla Mundial")

pestaña1, pestaña2, pestaña3, pestaña4 = st.tabs(["Tabla General", "Predicciones por Fecha", "VAR", "Segunda Ronda"])

########################################################################################################
with pestaña1:
    st.subheader("Clasificación General")
    st.write(f"Participantes : {len(participantes)}")
    st.write(f"Pozo: $880.000")

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

    col_izq, col_der1, col_der2 = st.columns([2, 1, 1])
    with col_izq:
        st.image("https://www.clarin.com/img/2015/06/17/HkGsvWbR7l_1256x620.jpg", width=300)
    with col_der1:
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSjkInHtjUDZSpVg4cHAYd7D-_RZ_CYB6njoA&s", width=150)
    with col_der2:
        st.image("https://pbs.twimg.com/profile_images/3434305374/cf5a6a6a0dcca079474f30b8a3b9c13b_400x400.gif", width=150)

########################################################################################################
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
        if st.button("▶") and st.session_state.fecha < 104:
            st.session_state.fecha += 1

    df_fecha_actual = tablas_fechas[st.session_state.fecha - 1]

    equipo_local  = df_fecha_actual.iloc[0]["A"]
    equipo_visita = df_fecha_actual.iloc[0]["D"]
    url_l = bandera_url(equipo_local)
    url_v = bandera_url(equipo_visita)

    # CORRECCIÓN: verificar fila por fila si tiene goles, sin depender de p_jugados
    fila_actual = df_resultado.iloc[st.session_state.fecha - 1]
    gol_l = fila_actual["B"]
    gol_v = fila_actual["C"]

    if pd.notna(gol_l) and pd.notna(gol_v):
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

    df_mostrar = df_fecha_actual[["Nombre", "B", "C", "F"]].rename(
        columns={"B": equipo_local, "C": equipo_visita, "F": "Puntos"}
    ).reset_index(drop=True)

    filas_pred = ""
    for _, row in df_mostrar.iterrows():
        puntos = int(row["Puntos"]) if pd.notna(row["Puntos"]) else "-"

        if puntos == 3:
            estilo_puntos = "background-color: rgba(0, 200, 83, 0.25);"
        elif puntos == 1:
            estilo_puntos = "background-color: rgba(255, 193, 7, 0.25);"
        elif puntos == 0:
            estilo_puntos = "background-color: rgba(244, 67, 54, 0.25);"
        else:
            estilo_puntos = ""

        # Mostrar la predicción tal cual si es válida, o "X" si no lo es
        val_l = row[equipo_local]
        val_v = row[equipo_visita]
        val_l_txt = str(int(float(val_l))) if es_numero(val_l) else ("-" if str(val_l).strip() == "-" else "X")
        val_v_txt = str(int(float(val_v))) if es_numero(val_v) else ("-" if str(val_v).strip() == "-" else "X")

        filas_pred += f"<tr><td>{row['Nombre']}</td><td>{val_l_txt}</td><td>{val_v_txt}</td><td style='{estilo_puntos}'>{puntos}</td></tr>"

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

########################################################################################################
with pestaña3:
    st.subheader("🔍 VAR - Verificación de Predicciones")

    nombres_disponibles = [nombre for nombre, _ in participantes]
    seleccionado = st.selectbox("Selecciona un participante:", nombres_disponibles)

    df_seleccionado = next(df for nombre, df in participantes if nombre == seleccionado)

    filas_var = ""
    total_puntos_var = 0

    for i in range(104):
        if i < len(df_resultado):
            equipo_local_v  = df_resultado.iloc[i]["A"]
            equipo_visita_v = df_resultado.iloc[i]["D"]
        else:
            equipo_local_v  = "-"
            equipo_visita_v = "-"

        if i < len(df_seleccionado):
            pred_l   = df_seleccionado.iloc[i]["B"]
            pred_v   = df_seleccionado.iloc[i]["C"]
            puntos_v = df_seleccionado.iloc[i]["F"]
        else:
            pred_l   = "-"
            pred_v   = "-"
            puntos_v = None

        # CORRECCIÓN: verificar fila por fila si tiene resultado real
        fila_res = df_resultado.iloc[i] if i < len(df_resultado) else None
        tiene_resultado = (
            fila_res is not None
            and pd.notna(fila_res["B"])
            and pd.notna(fila_res["C"])
        )

        if tiene_resultado:
            res_l        = int(fila_res["B"])
            res_v        = int(fila_res["C"])
            puntos_texto = str(int(puntos_v)) if pd.notna(puntos_v) else "-"
            if pd.notna(puntos_v):
                total_puntos_var += int(puntos_v)
        else:
            res_l        = "-"
            res_v        = "-"
            puntos_texto = "-"

        if puntos_texto == "3":
            estilo_fila = "background-color: rgba(0, 200, 83, 0.20);"
        elif puntos_texto == "1":
            estilo_fila = "background-color: rgba(255, 193, 7, 0.20);"
        elif puntos_texto == "0":
            estilo_fila = "background-color: rgba(244, 67, 54, 0.20);"
        else:
            estilo_fila = ""

        # CORRECCIÓN: si no es un número válido (p. ej. "X"), no intentar int(), mostrar "X"
        pred_l_txt = str(int(float(pred_l))) if es_numero(pred_l) else ("-" if str(pred_l).strip() == "-" else "X")
        pred_v_txt = str(int(float(pred_v))) if es_numero(pred_v) else ("-" if str(pred_v).strip() == "-" else "X")

        filas_var += (
            f"<tr style='{estilo_fila}'>"
            f"<td style='padding:6px;'>{equipo_local_v}</td>"
            f"<td style='padding:6px;'>{equipo_visita_v}</td>"
            f"<td style='padding:6px;'>{pred_l_txt}</td>"
            f"<td style='padding:6px;'>{pred_v_txt}</td>"
            f"<td style='padding:6px;'>{res_l}</td>"
            f"<td style='padding:6px;'>{res_v}</td>"
            f"<td style='padding:6px; font-weight:bold;'>{puntos_texto}</td>"
            f"</tr>"
        )

    html_var = (
        "<div style='background-color:#0e1117; padding:10px;'>"
        "<table style='width:100%; text-align:center; border-collapse:collapse; font-family:sans-serif; color:white;'>"
        "<thead>"
        "<tr style='background-color: rgba(128,128,128,0.15);'>"
        f"<th colspan='7' style='padding:10px; font-size:1.1em;'>Total puntos: {total_puntos_var}</th>"
        "</tr>"
        "<tr>"
        "<th colspan='2' style='padding:8px; border-bottom: 2px solid gray;'>Partido</th>"
        "<th colspan='2' style='padding:8px; border-bottom: 2px solid gray;'>Predicción</th>"
        "<th colspan='2' style='padding:8px; border-bottom: 2px solid gray;'>Resultado</th>"
        "<th style='padding:8px; border-bottom: 2px solid gray;'>Puntos</th>"
        "</tr>"
        "<tr style='font-size:0.85em; color: gray;'>"
        "<th style='padding:4px;'>Local</th>"
        "<th style='padding:4px;'>Visita</th>"
        "<th style='padding:4px;'>Local</th>"
        "<th style='padding:4px;'>Visita</th>"
        "<th style='padding:4px;'>Local</th>"
        "<th style='padding:4px;'>Visita</th>"
        "<th style='padding:4px;'></th>"
        "</tr>"
        "</thead>"
        f"<tbody>{filas_var}</tbody>"
        "</table>"
        "</div>"
    )

    components.html(html_var, height=2200, scrolling=True)


########################################################################################################
with pestaña4:
    st.subheader("Segunda Ronda")
    st.divider()

    # --- 8avos (parte 1) ---
    st.markdown("<h3 style='text-align:center; margin-bottom:8px;'>8avos (parte 1)</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center; margin-bottom:24px;'>"
        "<a href='https://forms.gle/8WFbk6tpb7vUXYqr6' target='_blank' "
        "style='font-size:1.2em; padding:12px 24px; background-color:#00C853; color:white; "
        "border-radius:8px; text-decoration:none;'>📝 Ir al formulario</a>"
        "</div>",
        unsafe_allow_html=True
    )

    
    st.markdown(
        "<div style='text-align:center; color:gray; font-size:0.85em; margin-top:6px;'>"
        "Los resultados de los partidos de 8vos (parte 1) se deben enviar antes de: Viernes 03/07 23:59hrs"
        "</div>",
        unsafe_allow_html=True
    )
