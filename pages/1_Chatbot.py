import pandas as pd
import requests
import streamlit as st

from recomendador import normalizar_respuesta, recomendar

st.set_page_config(page_title="Chatbot de música", page_icon="🎧")


def chatbot_configurado():
    """Dice si están los secretos para hablar con n8n."""
    try:
        return bool(st.secrets["N8N_WEBHOOK_URL"]) and bool(st.secrets["N8N_API_KEY"])
    except Exception:
        return False


if not chatbot_configurado():
    st.title("🎧 Chatbot de recomendaciones")
    st.info(
        "El chatbot solo funciona en la demostración local, cuando n8n está encendido. "
        "En esta versión publicada no está conectado."
    )
    st.stop()


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


def filtros_activos(filtros):
    """Deja solo los filtros que realmente restringen algo."""
    return {k: v for k, v in filtros.items() if v not in (None, [], 0, False, "")}


def mostrar_filtros(filtros):
    """Muestra en un desplegable los filtros que usó el asistente."""
    with st.expander("Ver filtros que usó el asistente"):
        activos = filtros_activos(filtros)
        if activos:
            st.json(activos)
        else:
            st.write("Sin filtros: se eligió entre todas las canciones.")


df = cargar_datos("spotify_limpio.csv")
generos = sorted(df["track_genre"].unique())

st.sidebar.header("Opciones")
descubrir = st.sidebar.checkbox("Descubrir música menos conocida")
st.sidebar.caption(
    "Por defecto el chatbot elige entre las canciones más populares que cumplen lo "
    "que pides. Si activas esta opción, elige entre las menos conocidas."
)

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
        if m.get("filtros") is not None:
            mostrar_filtros(m["filtros"])

pregunta = st.chat_input("¿Qué quieres escuchar?")

if pregunta:
    historial = [{"role": m["role"], "content": m["content"]} for m in st.session_state.mensajes]
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.write(pregunta)

    with st.chat_message("assistant"):
        filtros = None
        try:
            with st.spinner("Pensando..."):
                texto, filtros = consultar_n8n(pregunta, historial, generos)
            tabla = recomendar(df, filtros, n=5, descubrir=descubrir)
            if texto is None:
                texto = "No pude entender la respuesta del asistente. Intenta decirlo de otra forma."
                filtros = None
            elif tabla.empty:
                texto += "\n\nNo encontré canciones con esas características. Prueba con una descripción distinta."
        except Exception:
            texto, tabla, filtros = "Hubo un problema al conectar con el asistente. Intenta de nuevo en un momento.", None, None
        st.write(texto)
        if tabla is not None and not tabla.empty:
            st.dataframe(tabla, hide_index=True)
        if filtros is not None:
            mostrar_filtros(filtros)

    st.session_state.mensajes.append(
        {"role": "assistant", "content": texto, "tabla": tabla, "filtros": filtros}
    )
