# Movie Recommendation System
import sqlite3
from flask import Flask, jsonify
from flask import request
from uuid import uuid4
from datetime import datetime



database = 'movies.db'
connection = sqlite3.connect(database)
cursor = connection.cursor()
create_query = '''CREATE TABLE movies (
  id             UUID PRIMARY KEY DEFAULT ,
  title          VARCHAR(255)   NOT NULL,
  genre          VARCHAR(50)    NOT NULL,
  release_year   INTEGER        NOT NULL CHECK (release_year >= 1888),
  status         VARCHAR(20)    NOT NULL DEFAULT 'unwatched'
                   CHECK (status IN ('unwatched', 'watching', 'watched')),
  rating         INTEGER        NULL CHECK (rating >= 1 AND rating <= 5),
  date_added     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  date_watched   TIMESTAMPTZ    NULL,
  description    TEXT           NULL,
  director       VARCHAR(150)   NULL,
  runtime_minutes INTEGER       NULL CHECK (runtime_minutes > 0),
  language       VARCHAR(50)    NULL,
  poster_url     VARCHAR(500)   NULL,
  source         VARCHAR(100)   NULL,
  priority       VARCHAR(10)    NOT NULL DEFAULT 'normal'
                   CHECK (priority IN ('high', 'normal', 'low')),
  notes          TEXT           NULL,
  CONSTRAINT uq_title_year UNIQUE (title, release_year)
);'''

cursor.execute(create_query)
connection.commit()

app = Flask(__name__)

# Endpoint to add a new movie
@app.route('/api/v1/movies', methods=['POST'])
def add_movie():
    if request.method == 'POST':
        data = request.get_json()

        if data is None:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        errors={}
        title = data.get('title')
        genre = data.get('genre')
        release_year = data.get('release_year')

        title = title.strip() 
        if not title :
            errors['title'] = 'Title cannot be empty.'
        elif len(title) > 255:
            errors['title'] = 'Title cannot exceed 255 characters.'
        
        
        genre = genre.strip() 
        if not genre:
            errors['genre'] = 'Genre is required.'
        elif genre not in genre:
            errors['genre'] = f'Genre must be from the accepted list'
        
        
        release_year.strip()
        current_year = datetime.now().year
        if not release_year:
            errors['release_year'] = 'Release year is required.'
        elif not isinstance(release_year, int):
            errors['release_year'] = 'Release year must be an integer.'
        elif release_year < 1888:
            errors['release_year'] = 'Release year must be 1888 or later.'
        elif release_year > current_year:
            errors['release_year'] = f'Release year cannot be in the future (must be {current_year} or earlier).'
        
        status = data.get('status', 'unwatched')
        rating = data.get('rating')
        description = data.get('description')
        director = data.get('director')
        runtime_minutes = data.get('runtime_minutes')
        language = data.get('language')
        poster_url = data.get('poster_url')
        source = data.get('source')
        priority = data.get('priority', 'normal')
        notes = data.get('notes')

        