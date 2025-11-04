# app.py
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image

# =========================
# CONFIG TMDB
# =========================
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyYWE2ZWRjNmFhY2I3YmRmYmY5ZmIzZTQwNTA1NzVhMiIsIm5iZiI6MTc2MTE2NzM3OS4xODksInN1YiI6IjY4Zjk0ODEzMmQ4MjliNDI0MzUzNjNmZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.8qNpyp-wtM85ZsTmrESFRwlizPY5cbe_Jyv5N2yef2Q"

# =========================
# FUNCIONES
# =========================
@st.cache_data
def cargar_datos():
    """Carga ambos datasets de clustering"""
    pca_df = pd.read_csv("movies_w_clusters/movies_clustered_pca_3d.csv")
    nmf_df = pd.read_csv("movies_w_clusters/nmf_movies_with_clusters.csv")
    return pca_df, nmf_df

def get_tmdb_poster(tmdb_id):
    """Devuelve la URL del poster original de TMDb"""
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?language=en-US"
        headers = {"accept": "application/json", "Authorization": f"Bearer {TMDB_API_KEY}"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            poster_path = data.get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception as e:
        st.error(f"Error TMDb {tmdb_id}: {e}")
    return None

def mostrar_poster(url):
    """Descarga y muestra el poster en Streamlit"""
    try:
        if url:
            r = requests.get(url)
            img = Image.open(BytesIO(r.content))
            st.image(img, width=150)
        else:
            st.warning("Poster no disponible")
    except Exception as e:
        st.warning(f"No se pudo cargar el poster: {e}")

def obtener_recomendaciones(pelicula_id, dataset, n=6):
    """
    Obtiene películas del mismo cluster excluyendo la película seleccionada
    """
    # Encontrar el cluster de la película seleccionada
    pelicula_info = dataset[dataset['tmdbId'] == pelicula_id]
    
    if pelicula_info.empty:
        return pd.DataFrame()
    
    cluster_id = pelicula_info['cluster'].iloc[0]
    
    # Filtrar películas del mismo cluster excluyendo la seleccionada
    recomendaciones = dataset[
        (dataset['cluster'] == cluster_id) & 
        (dataset['tmdbId'] != pelicula_id)
    ]
    
    return recomendaciones.head(n)

def mostrar_info_pelicula(pelicula_info):
    """Muestra la información de una película"""
    st.write(f"**Título:** {pelicula_info['title'].iloc[0]}")
    st.write(f"**Géneros:** {pelicula_info['genres'].iloc[0]}")
    st.write(f"**Cluster:** {pelicula_info['cluster'].iloc[0]}")
    st.write(f"**TMDb ID:** {pelicula_info['tmdbId'].iloc[0]}")

# =========================
# CARGA DE DATOS
# =========================
pca_df, nmf_df = cargar_datos()

# Combinar todos los títulos para la búsqueda
todos_los_titulos = pd.concat([pca_df['title'], nmf_df['title']]).unique()

# =========================
# INTERFAZ STREAMLIT
# =========================
st.set_page_config(page_title="Sistema de Recomendación de Películas", layout="wide")

st.title("🎬 Sistema de Recomendación de Películas")
st.write("Encuentra películas similares usando diferentes algoritmos de clustering")

# Sidebar para configuración
st.sidebar.title("⚙️ Configuración")

# Selección de algoritmo de clustering
algoritmo = st.sidebar.selectbox(
    "Selecciona el algoritmo de clustering:",
    ["PCA", "NMF"],
    help="PCA: Basado en componentes principales | NMF: Basado en factorización de matrices no negativas"
)

# Seleccionar dataset según algoritmo
dataset = pca_df if algoritmo == "PCA" else nmf_df

# Número de recomendaciones
num_recomendaciones = st.sidebar.slider(
    "Número de recomendaciones:",
    min_value=3,
    max_value=12,
    value=6
)

# Barra de búsqueda principal
st.subheader("🔍 Buscar Película")
pelicula_buscada = st.selectbox(
    "Selecciona una película:",
    options=todos_los_titulos,
    index=0,
    help="Escribe para buscar en el catálogo completo"
)

if pelicula_buscada:
    # Buscar la película en el dataset seleccionado
    pelicula_info = dataset[dataset['title'] == pelicula_buscada]
    
    if not pelicula_info.empty:
        # Mostrar información de la película seleccionada
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🎭 Película Seleccionada")
            tmdb_id = pelicula_info['tmdbId'].iloc[0]
            poster_url = get_tmdb_poster(tmdb_id)
            mostrar_poster(poster_url)
        
        with col2:
            st.subheader("📋 Información")
            mostrar_info_pelicula(pelicula_info)
        
        # Obtener recomendaciones
        st.subheader(f"🎯 Películas representativas del cluster {pelicula_info['cluster']}")
        st.subheader(f"(Cluster {algoritmo})")
        recomendaciones = obtener_recomendaciones(tmdb_id, dataset, num_recomendaciones)
        
        if not recomendaciones.empty:
            # Mostrar recomendaciones en grid
            cols = st.columns(3)
            
            for idx, (_, pelicula) in enumerate(recomendaciones.iterrows()):
                with cols[idx % 3]:
                    with st.container():
                        st.write(f"**{pelicula['title']}**")
                        
                        # Mostrar poster
                        rec_poster_url = get_tmdb_poster(pelicula['tmdbId'])
                        if rec_poster_url:
                            st.image(rec_poster_url, width=120)
                        else:
                            st.info("🎬 Poster no disponible")
                        
                        st.write(f"*Géneros:* {pelicula['genres']}")
                        st.write(f"*Cluster:* {pelicula['cluster']}")
                        st.markdown("---")
        else:
            st.info("No se encontraron recomendaciones para esta película.")
    
    else:
        st.warning("Película no encontrada en el dataset seleccionado.")

# Información adicional en el sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Acerca de")
st.sidebar.info("""
**Algoritmos disponibles:**
- **PCA**: Reducción de dimensionalidad por componentes principales
- **NMF**: Factorización de matrices no negativas

Las recomendaciones se basan en películas del mismo cluster.
""")

# Estadísticas en el sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Estadísticas")
st.sidebar.write(f"**Total de películas:** {len(dataset)}")
st.sidebar.write(f"**Clusters {algoritmo}:** {dataset['cluster'].nunique()}")
st.sidebar.write(f"**Películas por cluster (avg):** {round(len(dataset) / dataset['cluster'].nunique(), 1)}")