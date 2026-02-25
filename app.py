# Movie Recommendation System
import sqlite3
from flask import Flask, jsonify
from flask import request
from uuid import uuid4
from datetime import datetime



database = 'movies.db'
connection = sqlite3.connect(database)
cursor = connection.cursor()
# Use a simple SQLite-compatible schema; UUID fields are stored as TEXT
create_query = '''CREATE TABLE IF NOT EXISTS movies (
  id TEXT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  genre VARCHAR(50) NOT NULL CHECK (genre IN ('Action','Comedy','Drama','Horror','Sci-Fi','Romance','Thriller','Documentary','Animation','Adventure')),
  release_year INTEGER NOT NULL CHECK (release_year >= 1888),
  status VARCHAR(20) NOT NULL DEFAULT 'unwatched' CHECK (status IN ('unwatched','watching','watched')),
  rating INTEGER NULL CHECK (rating >= 1 AND rating <= 5),
  date_added DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_watched DATETIME NULL,
  description TEXT NULL,
  director VARCHAR(150) NULL,
  runtime_minutes INTEGER NULL CHECK (runtime_minutes > 0),
  language VARCHAR(50) NULL,
  poster_url VARCHAR(500) NULL,
  source VARCHAR(100) NULL,
  priority VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (priority IN ('high','normal','low')),
  notes TEXT NULL,
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
        

        # Required fields validation
        errors=[]
        title = data.get('title')
        genre = data.get('genre')
        release_year = data.get('release_year')
        status = data.get('status')
        allowed_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Romance', 'Thriller', 'Documentary', 'Animation', 'Adventure']

       
        if not title :
            errors.append({"field": "title", "message": "Title cannot be empty."})
        elif len(title.strip()) > 255:
            errors.append({"field": "title", "message": "Title cannot exceed 255 characters."})

        
        
        
        if not genre:
            errors.append({"field": "genre", "message": "Genre is required."})
        elif  genre.strip() not in allowed_genres:
            errors.append({"field": "genre", "message": f'Genre must be from the accepted list: {", ".join(allowed_genres)}'})
        
        
        
        current_year = datetime.now().year
        if not release_year:
            errors.append({"field": "release_year", "message": "Release year is required."})
        elif not isinstance(release_year, int):
            errors.append({"field": "release_year", "message": "Release year must be an integer."})     
        elif release_year < 1888:
            errors.append({"field": "release_year", "message": "Release year must be 1888 or later."})
        elif release_year > current_year:
            errors.append({"field": "release_year", "message": f'Release year cannot be in the future (must be {current_year} or earlier).'})
        
        if not status:
            status = 'unwatched'  
        elif status not in ['unwatched', 'watching', 'watched']:
                errors.append({"field": "status", "message": f'Status must be one of: unwatched, watching, watched.'})


        # Optional fields validation
        rating = data.get('rating')
        director= data.get('director')
        runtime_minutes = data.get('runtime_minutes')
        poster_url = data.get('poster_url')
        priority = data.get('priority')
        notes = data.get('notes')
        cast= data.get('cast')
        description = data.get('description')

        if rating is not None:
            if not isinstance(rating, int) or isinstance(rating, bool):
                errors.append({"field": "rating", "message": "Rating must be an integer."})
            elif rating < 1 or rating > 5:
                errors.append({"field": "rating", "message": "Rating must be between 1 and 5."})
        
        if description is not None:
            if not isinstance(description, str):
                errors.append({"field": "description", "message": "Description must be a string."})
            elif len(description.strip()) >  2000:
                errors.append({"field": "description", "message": "Description cannot exceed 2000 characters."})


        if cast is not None:
            if not isinstance(cast, list):
                errors.append({"field": "cast", "message": "Cast must be a array of strings."})

            elif len(cast) > 10:
                errors.append({"field": "cast", "message": "Cast cannot have more than 10 members."}) 
            else:
                for member in cast:
                    if not isinstance(member, str):
                        errors.append({"field": "cast", "message": "Each cast member must be a string."})
                    elif len(member.strip()) > 100:
                        errors.append({"field": "cast", "message": "Each cast member cannot exceed 100 characters."})   
                        break
        
        if runtime_minutes is not None:
            if not isinstance(runtime_minutes, int) or isinstance(runtime_minutes, bool):
                errors.append({"field": "runtime_minutes", "message": "Runtime minutes must be an integer."})
            elif runtime_minutes <= 0 or runtime_minutes > 600:
                errors.append({"field": "runtime_minutes", "message": "Runtime minutes must be greater than 0 and less than or equal to 600."})
        
        if poster_url is not None:
            if not isinstance(poster_url, str):
                errors.append({"field": "poster_url", "message": "Poster URL must be a string."})
            elif not poster_url.startswith(("http://", "https://")):
                errors.append({"field": "poster_url", "message": "Poster URL must be a valid HTTP or HTTPS URL."})
        
        if priority is not None:
            if priority not in ['high', 'normal', 'low']:
                errors.append({"field": "priority", "message": f'Priority must be one of: high, normal, low.'})

        if notes is not None:
            if not isinstance(notes, str):
                errors.append({"field": "notes", "message": "Notes must be a string."})
            elif len(notes.strip()) > 2000:
                errors.append({"field": "notes", "message": "Notes cannot exceed 2000 characters."})

        if errors:
            return jsonify({
            "success": False,
            "message": "Validation failed",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": errors        
            },
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "request_id": str(uuid4())
            }
            }), 400
        
        
        # Insert movie into database
        insert_query = '''INSERT INTO movies (id, title, genre, release_year, status, rating, description, director, runtime_minutes, poster_url, priority, notes)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        movie_id = str(uuid4())
        cursor.execute(insert_query, (movie_id, title.strip(), genre.strip(), release_year, status, rating, description, director, runtime_minutes, poster_url, priority, notes))
        connection.commit()
        return jsonify({
    "success": True,
    "message": "Movie added successfully",
    "data": {
        "id": movie_id,            
        "title": title,
        "genre": genre,
        "release_year": release_year,
        "status": status,
        "rating": rating,
        "date_added": datetime.now().isoformat(),    
        "director": director,    
        "runtime_minutes": runtime_minutes,
        "poster_url": poster_url,
        "priority": priority,
        "notes": notes

    },
    "meta": {
        "timestamp": datetime.now().isoformat(),
        "request_id": str(uuid4())
    }
}), 201

        