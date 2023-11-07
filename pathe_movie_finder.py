import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
import os
from pathe_scraper import *

# Extract movie names from Json and output as DF
def extract_movie_names(data):
    movie_names = []
    for item in data:
        # If the item's '@type' is 'ScreeningEvent'...
        if item.get('@type') == 'ScreeningEvent':
            # Iterate over each movie in 'workPresented'
            for movie in item['workPresented']:
                movie_names.append(movie['name'])
    return pd.DataFrame(movie_names, columns=['Movie Name'])

# Remove any non movie info and drop duplicates
def clean_movie_names(df):
    pattern = r" \(.*\)"
    df['Cleansed Movie Name'] = df['Movie Name'].apply(lambda name: re.sub(pattern, "", name))
    df_unique = df.drop_duplicates(subset='Cleansed Movie Name')
    return df_unique[['Cleansed Movie Name']]

# Interface with the movie DB API to get a score for the movies
def get_tmdb_info(movie_name, api_key):
    global data, score, response
    base_url = "https://api.themoviedb.org/3"
    search_url = f"{base_url}/search/movie?api_key={api_key}&query={movie_name}"

    response = requests.get(search_url)
    data = response.json()

    if data['results']:
        # Take the first (and best match) if there are multiple
        first_movie = data['results'][0]
        movie_id = first_movie['id']

        movie_url = f"{base_url}/movie/{movie_id}?api_key={api_key}"
        response = requests.get(movie_url)
        data = response.json()

        score = data.get('vote_average')
        votes = data.get('vote_count')

    else:
        score = None
        votes = None

    return score, votes

# Function to find and append movie scores
def find_score(df_cleansed, api_key):
    # Get movie scores and create a new dataframe with movie names and scores
    movie_scores = []
    movie_votes = []
    for movie_name in df_cleansed['Cleansed Movie Name']:
        score, votes = get_tmdb_info(movie_name, api_key)
        movie_scores.append(score)
        movie_votes.append(votes)

    # Add the scores as a new column to the cleansed DataFrame
    df_cleansed['Score'] = movie_scores
    df_cleansed['Score'] = df_cleansed['Score'].round(1)
    
    df_cleansed['Votes'] = movie_votes
    
    # Add a column for movies with votes above 100
    df_cleansed['Votes_above_100'] = df_cleansed['Votes'] >= 100

    # Sort the DataFrame by 'Votes_above_100' (False first, then True), then by 'Score' in descending order
    df_cleansed = df_cleansed.sort_values(['Votes_above_100', 'Score'], ascending=[False, False])
    
    return df_cleansed

def main(url, api_key):
    df_scored = find_score(
        clean_movie_names(
            extract_movie_names(
                parse_html_for_json_movie(
                    get_theater_html_content(url)
                )
            )
        ),
        api_key
    )
    print(df_scored)
    
if __name__ == "__main__":
    url = "https://www.pathe.nl/bioscoop/eindhoven"
    tmdb_api_key = os.environ.get('tmdb_api')
    main(url, tmdb_api_key)
