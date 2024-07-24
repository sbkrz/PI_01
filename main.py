from fastapi import FastAPI
import pandas as pd
import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List


movies = pd.read_csv('./movies_dataset.csv')
movies_credits = pd.read_csv('./credits.csv')
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/cantidad_filmaciones_mes/{mes}")
def cantidad_filmaciones_mes(mes):
    meses_ingles = {
        'enero': 'January',
        'febrero': 'February',
        'marzo': 'March',
        'abril': 'April',
        'mayo': 'May',
        'junio': 'June',
        'julio': 'July',
        'agosto': 'August',
        'septiembre': 'September',
        'octubre': 'October',
        'noviembre': 'November',
        'diciembre': 'December'
    }
    mes_en_ingles = meses_ingles.get(mes.lower())
    if mes_en_ingles is None:
        return "Mes no válido. Por favor, ingrese un mes válido en español."
    movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
    movies_mes = movies[movies['release_date'].dt.strftime('%B').str.lower() == mes_en_ingles.lower()]
    cantidad = len(movies_mes) 
    
    return f"{cantidad} películas fueron estrenadas en el mes de {mes.capitalize()}."

@app.get("/cantidad_filmaciones_dia/{dia}")
def cantidad_filmaciones_dia(Dia):
    dias_ingles = {
        'lunes': 'Monday',
        'martes': 'Tuesday',
        'miércoles': 'Wednesday',
        'jueves': 'Thursday',
        'viernes': 'Friday',
        'sábado': 'Saturday',
        'domingo': 'Sunday',
    }
    
    dias_en_ingles = dias_ingles.get(Dia.lower())
    if dias_en_ingles is None:
        return "Día no válido. Por favor, ingrese un día válido en español."
    
    movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
    movies_dia = movies[movies['release_date'].dt.strftime('%A').str.lower() == dias_en_ingles.lower()]
    cantidad = len(movies_dia)
    
    return f"{cantidad} películas fueron estrenadas en el día {Dia.capitalize()}."

@app.get("/score_titulo/{titulo}")
def score_titulo(titulo_de_la_filmacion):
    movie = movies[movies['title'].str.lower() == titulo_de_la_filmacion.lower()] 
    
    if movie.empty:
        return f"No se encontró la película con el título '{titulo_de_la_filmacion}' en la base de datos."
    
    title = movie['title'].values[0]
    release_year = movie['release_year'].values[0]
    score = movie['popularity'].values[0]
    
    return f"La película '{title}' fue estrenada en el año {release_year} con un score/popularidad de {score}."

@app.get("/votos_titulo/{titulo}")
def votos_titulo(titulo_de_la_filmacion):
    pelicula = movies[movies['title'].str.lower() == titulo_de_la_filmacion.lower()] #Buscamos la película por título
    
    if pelicula.empty:
        return f"No se encontró ninguna película con el título '{titulo_de_la_filmacion}'."
    
    votos_totales = pelicula['vote_count'].iloc[0]
    if votos_totales < 2000: #Verificamos si tiene al menos 2000 valoraciones
        return f"La película '{titulo_de_la_filmacion}' tiene menos de 2000 valoraciones ({votos_totales} valoraciones en total). No cumple con la condición requerida."
    
    promedio_votos = pelicula['vote_average'].iloc[0] #Calculamos el promedio de votos
    
    mensaje = f"La película '{titulo_de_la_filmacion}' fue estrenada en el año {pelicula['release_year'].iloc[0]}. "
    mensaje += f"La misma cuenta con un total de {votos_totales} valoraciones, con un promedio de {promedio_votos:.1f}."
    
    return mensaje

def load_json(x):
    if isinstance(x, str):  
        try:
            return json.loads(x.replace("'", '"'))
        except json.JSONDecodeError:
            return []
    return []
movies_credits['cast'] = movies_credits['cast'].apply(load_json)

movies_combined = pd.concat([movies_credits.reset_index(drop=True), movies[['return']].reset_index(drop=True)], axis=1)

@app.get("/get_actor/{nombre_actor}")
def get_actor(nombre_actor):
    actor_found = False
    total_films = 0
    total_return = 0.0

    for index, row in movies_combined.iterrows():
        for actor in row['cast']:
            if actor['name'] == nombre_actor:
                actor_found = True
                total_films += 1
                total_return += row.get('return', 0.0)

    if not actor_found:
        return f"El actor {nombre_actor} no ha sido encontrado en el dataset."

    if total_films == 0:
        return f"El actor {nombre_actor} no ha participado en ninguna filmación."

    average_return = total_return / total_films
    return f"El actor {nombre_actor} ha participado en {total_films} filmaciones. Ha conseguido un retorno total de {total_return} con un promedio de {average_return} por filmación."


@app.get("/get_director/{nombre_director}")
def get_director(nombre_director):
    nombre_director = nombre_director.lower() 
    peliculas_director = []

    for index, row in movies_credits.iterrows():
        crew = load_json(row['crew'])
        
        if isinstance(crew, list):
            for member in crew:
                if member['job'].lower() == 'director' and nombre_director in member['name'].lower():
                    movie_info = {
                        'titulo': row['title'],
                        'fecha_lanzamiento': row['release_date'],
                        'retorno': row['return'],
                        'costo': row['budget'],
                        'ganancia': row['revenue']
                    }
                    peliculas_director.append(movie_info)
                    break  
    
    if len(peliculas_director) > 0:
        mensaje_retorno = f"El director {nombre_director.capitalize()} ha dirigido las siguientes películas:\n"
        for pelicula in peliculas_director:
            mensaje_retorno += f"Título: {pelicula['titulo']}, Fecha de Lanzamiento: {pelicula['fecha_lanzamiento']}, " \
                               f"Retorno: {pelicula['retorno']}, Costo: {pelicula['costo']}, Ganancia: {pelicula['ganancia']}\n"
    else:
        mensaje_retorno = f"El director {nombre_director.capitalize()} no ha dirigido ninguna película."
    
    return mensaje_retorno


movies['overview'] = movies['overview'].fillna('')
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies['overview'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

@app.get("/recomendacion")
def recomendacion(title):
    idx = movies.index[movies['title'] == title].tolist()[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6] 
    movie_indices = [i[0] for i in sim_scores]
    return movies['title'].iloc[movie_indices]

# if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run(app, host="127.0.0.1", port=8000)
