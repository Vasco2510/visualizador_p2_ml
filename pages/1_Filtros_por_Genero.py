# pages/1_Filtros_por_Genero.py
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image

TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyYWE2ZWRjNmFhY2I3YmRmYmY5ZmIzZTQwNTA1NzVhMiIsIm5iZiI6MTc2MTE2NzM3OS4xODksInN1YiI6IjY4Zjk0ODEzMmQ4MjliNDI0MzUzNjNmZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.8qNpyp-wtM85ZsTmrESFRwlizPY5cbe_Jyv5N2yef2Q"

@st.cache_data
def cargar_datos():
    pca_df = pd.read_csv("pca_movies_with_clusters.csv")
    nmf_df = pd.read_csv("nmf_movies_with_clusters.csv")
    return pca_df, nmf_df

@st.cache_data(ttl=3600)  # Cache de 1 hora para posters
def get_tmdb_poster(tmdb_id):
    """Versión mejorada con mejor manejo de errores"""
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?language=en-US"
        headers = {
            "accept": "application/json", 
            "Authorization": f"Bearer {TMDB_API_KEY}"
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            poster_path = data.get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w200{poster_path}"
        else:
            st.sidebar.warning(f"API error para {tmdb_id}: {r.status_code}")
    except Exception as e:
        st.sidebar.warning(f"Error obteniendo poster {tmdb_id}: {str(e)[:50]}...")
    return None

def mostrar_poster_grid(poster_url, titulo, width=80):
    """Muestra un poster con manejo de errores"""
    try:
        if poster_url:
            response = requests.get(poster_url, timeout=10)
            img = Image.open(BytesIO(response.content))
            st.image(img, width=width, caption=titulo[:20] + "..." if len(titulo) > 20 else titulo)
        else:
            st.error("❌ No poster")
    except:
        st.error("❌ Error carga")

# =========================
# INTERFAZ DE FILTRO POR GÉNERO
# =========================
st.set_page_config(page_title="Filtrar por Género", layout="wide")
st.title("🎞️ Filtrar Películas por Género")

# Cargar datos
pca_df, nmf_df = cargar_datos()

# DEBUG: Mostrar estructura de datos
with st.expander("🔍 Debug - Estructura de datos"):
    st.write("PCA DataFrame shape:", pca_df.shape)
    st.write("NMF DataFrame shape:", nmf_df.shape)
    if not pca_df.empty:
        st.write("Columnas PCA:", pca_df.columns.tolist())
        st.write("Primeras filas PCA:", pca_df.head(2))
        st.write("Ejemplo de géneros:", pca_df['genres'].head(5).tolist())

# Selección de algoritmo
algoritmo = st.sidebar.selectbox("Algoritmo de clustering:", ["PCA", "NMF"])
dataset = pca_df if algoritmo == "PCA" else nmf_df

# Extraer géneros únicos de manera más robusta
try:
    # Dividir géneros y aplanar la lista
    todos_generos = set()
    for genre_list in dataset["genres"].dropna():
        if '|' in str(genre_list):
            todos_generos.update(genre_list.split('|'))
        else:
            todos_generos.add(genre_list)
    
    todos_generos = sorted([g for g in todos_generos if g and g != '(no genres listed)'])
    
except Exception as e:
    st.error(f"Error procesando géneros: {e}")
    todos_generos = []

# Mostrar información de géneros
st.sidebar.write(f"📊 **{len(todos_generos)}** géneros encontrados")
st.sidebar.write(f"🎬 **{len(dataset)}** películas en total")

# Selección de géneros
if todos_generos:
    generos_sel = st.multiselect(
        "Selecciona uno o varios géneros:", 
        todos_generos,
        help="Puedes seleccionar múltiples géneros"
    )
    
    if generos_sel:
        st.success(f"Buscando películas con: **{', '.join(generos_sel)}**")
        
        # Filtrar dataset - versión mejorada
        def contiene_generos(genres_str, generos_buscar):
            """Verifica si alguno de los géneros buscados está en la cadena de géneros"""
            if pd.isna(genres_str):
                return False
            pelicula_generos = set(genres_str.split('|'))
            return any(gen_buscar in pelicula_generos for gen_buscar in generos_buscar)
        
        mask = dataset["genres"].apply(contiene_generos, generos_buscar=generos_sel)
        filtradas = dataset[mask]
        
        st.write(f"**🎬 {len(filtradas)} películas encontradas**")
        
        if not filtradas.empty:
            # Mostrar estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Películas encontradas", len(filtradas))
            with col2:
                st.metric("Clusters distintos", filtradas['cluster'].nunique())
            with col3:
                st.metric("Género principal", generos_sel[0])
            
            # Seleccionar 10 películas aleatorias o las primeras 10
            mostrar_count = min(10, len(filtradas))
            peliculas_mostrar = filtradas.head(20).sample(n=mostrar_count) if len(filtradas) > mostrar_count else filtradas
            
            st.subheader(f"🎭 {mostrar_count} Posters de Películas")
            
            # Mostrar en grid de 5 columnas para posters pequeños
            cols = st.columns(5)
            
            for idx, (_, row) in enumerate(peliculas_mostrar.iterrows()):
                if idx >= 10:  # Máximo 10 posters
                    break
                    
                with cols[idx % 5]:
                    poster_url = get_tmdb_poster(row["tmdbId"])
                    mostrar_poster_grid(poster_url, row['title'], width=80)
                    # st.caption(f"**{row['title']}**")
                    with st.expander("ℹ️"):
                        st.write(f"**{row['title']}**")
                        st.write(f"Géneros: {row['genres']}")
                        st.write(f"Cluster: {row['cluster']}")
                        st.write(f"ID: {row['tmdbId']}")
        else:
            st.warning("No se encontraron películas con los géneros seleccionados.")
            
    else:
        st.info("👆 Selecciona al menos un género para ver películas.")
        
else:
    st.error("No se pudieron cargar los géneros. Revisa la estructura del dataset.")

# Footer informativo
st.markdown("---")
st.caption("💡 Tip: Selecciona múltiples géneros para encontrar películas que combinen varios estilos")