# ¿Qué pesa más en la popularidad: el género o la música?

Dashboard interactivo en Streamlit sobre el Spotify Tracks Dataset (Kaggle, autor maharshipandya).

**App desplegada:** https://spotify-genero-popularidad.streamlit.app/

## Pregunta guía

¿Qué pesa más en la popularidad de una canción: sus características musicales (bailabilidad, energía, positividad, acústica) o el género al que pertenece?

## Hallazgos principales

- El género explica entre el 25% y el 38% de la variabilidad de la popularidad, mientras que la bailabilidad explica menos del 0,5%.
- Una parte importante de las canciones tiene popularidad 0 y se reparte de forma muy desigual entre géneros; quitarlas cambia el ranking.
- Al mezclar géneros aparece una correlación que dentro de cada género casi no existe.

## Cómo ejecutarlo

```
pip install -r requirements.txt
streamlit run app.py
```

## Archivos

- app.py: aplicación Streamlit
- requirements.txt: librerías necesarias
- spotify_limpio.csv: dataset limpio (una fila por canción dentro de cada género)

## Limitaciones

El dataset es una muestra de cerca de 1.000 canciones por género, no refleja cuántas canciones existen realmente de cada uno. No se conoce el motivo de las canciones con popularidad 0.
