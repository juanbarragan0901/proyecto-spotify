"""Funciones del chatbot recomendador (sin dependencias de Streamlit)."""
import json
import re

import pandas as pd

CARACTERISTICAS = ["danceability", "energy", "valence", "acousticness"]
COLUMNAS_TABLA = ["track_name", "artists", "track_genre", "popularity"]


def extraer_json(texto):
    """Busca el primer objeto JSON dentro del texto que devuelve el modelo.

    Devuelve un diccionario o None si no encuentra un JSON válido.
    """
    if not isinstance(texto, str):
        return None
    limpio = texto.replace("```json", "").replace("```", "")
    coincidencia = re.search(r"\{.*\}", limpio, re.DOTALL)
    if not coincidencia:
        return None
    try:
        return json.loads(coincidencia.group(0))
    except json.JSONDecodeError:
        return None


def normalizar_respuesta(datos):
    """Convierte lo que devuelve n8n en (respuesta, filtros).

    n8n puede devolver una lista, un objeto con los campos directos o un
    objeto con el texto del modelo en 'output' o 'text'.
    """
    if isinstance(datos, list) and datos:
        datos = datos[0]
    if not isinstance(datos, dict):
        return None, {}
    if "filtros" not in datos:
        for clave in ("output", "text", "respuesta"):
            interno = extraer_json(datos.get(clave))
            if interno is not None:
                datos = interno
                break
    respuesta = datos.get("respuesta")
    filtros = datos.get("filtros")
    if not isinstance(filtros, dict):
        filtros = {}
    return respuesta, filtros


def _numero(valor):
    """Convierte a float y devuelve None si no se puede."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def recomendar(df, filtros, n=5, semilla=None):
    """Filtra el DataFrame con los filtros del modelo y elige n canciones.

    Solo usa claves conocidas y valores válidos, así que el modelo nunca
    puede inventar canciones ni columnas.
    """
    resultado = df

    validos = set(df["track_genre"].unique())
    generos = [g for g in filtros.get("generos", []) if g in validos]
    if generos:
        resultado = resultado[resultado["track_genre"].isin(generos)]

    for col in CARACTERISTICAS:
        minimo = _numero(filtros.get(f"{col}_min"))
        maximo = _numero(filtros.get(f"{col}_max"))
        if minimo is not None:
            resultado = resultado[resultado[col] >= minimo]
        if maximo is not None:
            resultado = resultado[resultado[col] <= maximo]

    pop_min = _numero(filtros.get("popularidad_min")) or 0
    resultado = resultado[resultado["popularity"] >= pop_min]

    if filtros.get("sin_explicitas") is True:
        resultado = resultado[~resultado["explicit"].astype(bool)]

    resultado = resultado.drop_duplicates(subset=["track_name", "artists"])
    if resultado.empty:
        return pd.DataFrame(columns=COLUMNAS_TABLA)

    # Se toman las 30 más populares y se sortean n para dar variedad
    candidatas = resultado.sort_values("popularity", ascending=False).head(30)
    elegidas = candidatas.sample(min(n, len(candidatas)), random_state=semilla)
    return elegidas[COLUMNAS_TABLA].reset_index(drop=True)