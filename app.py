import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Spotify: ¿género o música?", layout="wide")

CARACTERISTICAS = {
    "Bailabilidad": "danceability",
    "Energía": "energy",
    "Positividad (valence)": "valence",
    "Acústica": "acousticness",
}


@st.cache_data
def cargar_datos(ruta):
    """Carga el CSV limpio."""
    return pd.read_csv(ruta)


def filtrar(df, excluir_ceros, rango):
    """Filtra por rango de popularidad y, opcionalmente, quita los ceros."""
    df = df[df["popularity"].between(rango[0], rango[1])]
    if excluir_ceros:
        df = df[df["popularity"] > 0]
    return df


def correlacion(df, columna):
    """Correlación de Pearson con la popularidad (NaN si no se puede calcular)."""
    if len(df) < 2 or df[columna].std() == 0 or df["popularity"].std() == 0:
        return float("nan")
    return float(np.corrcoef(df[columna], df["popularity"])[0, 1])


df = cargar_datos("spotify_limpio.csv")

st.title("🎵 ¿Qué pesa más en la popularidad: el género o la música?")

# --- Widgets ---
st.sidebar.header("Filtros")
todos = sorted(df["track_genre"].unique())
generos = st.sidebar.multiselect(
    "Géneros", todos, default=["pop", "rock", "jazz", "salsa", "k-pop"]
)
excluir_ceros = st.sidebar.checkbox("Excluir canciones con popularidad 0")
nombre = st.sidebar.selectbox("Característica musical", list(CARACTERISTICAS))
rango = st.sidebar.slider("Rango de popularidad", 0, 100, (0, 100))

if not generos:
    st.warning("Selecciona al menos un género.")
    st.stop()

df_gen = df[df["track_genre"].isin(generos)]
df_f = filtrar(df_gen, excluir_ceros, rango)
if df_f.empty:
    st.warning("No hay canciones con esos filtros.")
    st.stop()

columna = CARACTERISTICAS[nombre]
r = correlacion(df_f, columna)

# --- Métricas ---
c1, c2, c3 = st.columns(3)
c1.metric("Canciones", f"{len(df_f):,}")
c2.metric("Popularidad media", f"{df_f['popularity'].mean():.1f}")
c3.metric(f"Correlación con {nombre}", "N/D" if np.isnan(r) else f"{r:.3f}")

# --- Visualizaciones ---
g1, g2, g3 = st.columns(3)

with g1:
    medias = df_f.groupby("track_genre")["popularity"].mean().sort_values()
    fig, ax = plt.subplots()
    ax.barh(medias.index, medias.values)
    ax.set_title("Popularidad media por género")
    ax.set_xlabel("Popularidad (0-100)")
    st.pyplot(fig)

with g2:
    pct = (df_gen["popularity"] == 0).groupby(df_gen["track_genre"]).mean() * 100
    pct = pct.sort_values()
    fig, ax = plt.subplots()
    ax.barh(pct.index, pct.values)
    ax.set_title("% de canciones con popularidad 0")
    ax.set_xlabel("%")
    st.pyplot(fig)

with g3:
    muestra = df_f.sample(min(3000, len(df_f)), random_state=1)
    fig, ax = plt.subplots()
    ax.scatter(muestra[columna], muestra["popularity"], s=6, alpha=0.3)
    ax.set_title(f"{nombre} vs. popularidad")
    ax.set_xlabel(nombre)
    ax.set_ylabel("Popularidad")
    st.pyplot(fig)

st.dataframe(df_f[["track_name", "artists", "track_genre", "popularity", columna]].head(100))