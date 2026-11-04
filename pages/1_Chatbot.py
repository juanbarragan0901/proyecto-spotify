import pandas as pd
import requests
import streamlit as st

from recomendador import normalizar_respuesta, recomendar

st.set_page_config(page_title="Chatbot de música", page_icon="🎧")


@st.cache_data
def cargar_datos(ruta):
    """Carga el CSV limpio."""
    return pd.read_csv(ruta)


def consultar_n8n(mensaje, historial, generos):
    """Envía el mensaje a n8n y devuelve (respuesta, filtros)."""
    respuesta = requests.post(
        st.secrets["N8N_WEBHOOK_URL"],
        json={"mensaje": mensaje, "historial": historial[-6:], "generos": generos},
        headers={"X-API-Key": st.secrets["N8N_API_KEY"]},
        timeout=60,
    )
    respuesta.raise_for_status()
    return normalizar_respuesta(respuesta.json())


df = cargar_datos("spotify_limpio.csv")
generos = sorted(df["track_genre"].unique())

st.title("🎧 Chatbot de recomendaciones")
st.caption(
    "Cuéntame qué quieres escuchar (por ejemplo: música tranquila para estudiar). "
    "Las canciones salen de nuestro dataset de Spotify."
)

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

for m in st.session_state.mensajes:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if m.get("tabla") is not None and not m["tabla"].empty:
            st.dataframe(m["tabla"], hide_index=True)

pregunta = st.chat_input("¿Qué quieres escuchar?")

if pregunta:
    historial = [{"role": m["role"], "content": m["content"]} for m in st.session_state.mensajes]
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.write(pregunta)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Pensando..."):
                texto, filtros = consultar_n8n(pregunta, historial, generos)
            tabla = recomendar(df, filtros, n=5)
            if texto is None:
                texto = "No pude entender la respuesta del asistente. Intenta decirlo de otra forma."
            elif tabla.empty:
                texto += "\n\nNo encontré canciones con esas características. Prueba con una descripción distinta."
        except Exception:
            texto, tabla = "Hubo un problema al conectar con el asistente. Intenta de nuevo en un momento.", None
        st.write(texto)
        if tabla is not None and not tabla.empty:
            st.dataframe(tabla, hide_index=True)

    st.session_state.mensajes.append({"role": "assistant", "content": texto, "tabla": tabla})
  
