import glob
import os
import pandas as pd
import numpy as np
import streamlit as st

# ---- FUNCIONES ----

def CALCULAR_PUNTOS(df_resultado, df_participante):
    df_resultado = df_resultado.reset_index(drop=True)
    df_participante = df_participante.reset_index(drop=True)
    
    df_participante["E"] = np.where(df_participante["B"] > df_participante["C"], "L",
                            np.where(df_participante["B"] < df_participante["C"], "V", "E"))
    
    df_participante["F"] = None
    
    n = len(df_resultado)
    
    condiciones = [
        (df_resultado["B"].values == df_participante["B"].values[:n]) & 
        (df_resultado["C"].values == df_participante["C"].values[:n]),
        (df_resultado["E"].values == df_participante["E"].values[:n])
    ]
    valores = [3, 1]
    
    df_participante.loc[:n-1, "F"] = np.select(condiciones, valores, default=None)
    return df_participante

def TABLA_PUNTAJES(participantes):
    resultados = []
    for nombre, df_participante in participantes:
        total_puntos = df_participante["F"].sum()
        total_exactos = (df_participante["F"] == 3).sum()
        resultados.append([nombre, total_puntos, total_exactos])
    df_tabla = pd.DataFrame(resultados, columns=["Nombre", "Puntos", "Exactos"])
    df_tabla = df_tabla.sort_values(by=["Puntos", "Exactos"], ascending=False)
    return df_tabla

def PREDICCIONES(participantes, total):
    tablas_fechas = []
    for i in range(total):
        tabla_fecha = []
        for nombre, df_participante in participantes:
            prediccion_b = df_participante.iloc[i]["B"]
            prediccion_c = df_participante.iloc[i]["C"]
            puntos_fila = df_participante.iloc[i]["F"]
            tabla_fecha.append([nombre, prediccion_b, prediccion_c, puntos_fila])
        df_fecha = pd.DataFrame(tabla_fecha, columns=["Nombre", "B", "C", "F"])
        tablas_fechas.append(df_fecha)
    return tablas_fechas

# ---- CÓDIGO PRINCIPAL ----

df_resultado = pd.read_excel("resultados.xlsx", header=None, names=["A","B","C","D","E","F","G","H"])
p_jugados = int(df_resultado["H"].count())
df_resultado["E"] = np.where(df_resultado["B"] > df_resultado["C"], "L",
                    np.where(df_resultado["B"] < df_resultado["C"], "V", "E"))

archivos = glob.glob("carpeta/*.xlsx")
participantes = []
for archivo in archivos:
    nombre = os.path.splitext(os.path.basename(archivo))[0]
    df_participante = pd.read_excel(archivo, header=None, names=["A","B","C","D","E","F","G","H"])
    df_participante = CALCULAR_PUNTOS(df_resultado, df_participante)
    participantes.append([nombre, df_participante])

total_partidos = len(participantes[0][1])
tablas_fechas = PREDICCIONES(participantes, total_partidos)


# ---- STREAMLIT ----

st.title("🏆 Polla Mundial")

pestaña1, pestaña2 = st.tabs(["Tabla General", "Predicciones por Fecha"])

with pestaña1:
    st.subheader("Clasificación General")
    st.dataframe(df_tabla, use_container_width=True)

with pestaña2:
    st.subheader("Predicciones por Fecha")

    if "fecha" not in st.session_state:
        st.session_state.fecha = 1

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("◀") and st.session_state.fecha > 1:
            st.session_state.fecha -= 1

    with col2:
        st.markdown(f"### Partido {st.session_state.fecha}")

    with col3:
        if st.button("▶") and st.session_state.fecha < 78:
            st.session_state.fecha += 1

    st.dataframe(tablas_fechas[st.session_state.fecha - 1], use_container_width=True)
