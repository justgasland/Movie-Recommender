# Movie Recommendation System
import sqlite3
from flask import Flask, jsonify
from flask import request, g
from uuid import uuid4
from datetime import datetime

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


database = 'movies.db'

# Use a simple SQLite-compatible schema; UUID fields are stored as TEXT
def init_db():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
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
    connection.close()



def get_db():
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    return connection





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
        else:
            # Insert movie into database
            insert_query = '''INSERT INTO movies (id, title, genre, release_year, status, rating, description, director, runtime_minutes, poster_url, priority, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            movie_id = str(uuid4())
            db = get_db()
            cur = db.cursor()
            cur.execute(insert_query, (movie_id, title.strip(), genre.strip(), release_year, status, rating, description, director, runtime_minutes, poster_url, priority, notes))
            db.commit()
            db.close()
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
        



# Endpoint to get all movies
@app.route('/api/v1/movies', methods=['GET'])

def get_movies():
    if request.method == 'GET': 
        db = get_db()
        cursor = db.cursor()
        query = 'SELECT * FROM movies WHERE 1=1'
        parameters = []
        
        genre = request.args.get('genre')
        status = request.args.get('status')
        rating_min= request.args.get('rating_min')
        rating_max= request.args.get('rating_max')
        q= request.args.get('q')

        
        sort_by= request.args.get('sort_by')
        sort_order= request.args.get('sort_order')

        page = request.args.get('page', 1)
        limit = request.args.get('limit', 20)

        rating_min=int(rating_min) if rating_min is not None else None
        rating_max=int(rating_max)if rating_max is not None else None
        
        page=int(page)
        limit=int(limit)
        
        
        if genre:
            query += ' AND genre = ?'
            parameters.append(genre)
        
        if status:
            query += ' AND status = ?'
            parameters.append(status)
        
        if rating_min is not None:
            query += ' AND rating >= ?'
            parameters.append(rating_min)
        
        if rating_max is not None:
            query += ' AND rating <= ?'
            parameters.append(rating_max)
        
        allowed_sort_fields = ['title', 'release_year', 'rating', 'date_watched', 'date_added']
        allowed_sort_orders = ['asc', 'desc']
        
        if q:
            query += ' AND (title LIKE ? OR description LIKE ?)'
            parameters.append(f'%{q}%')
            parameters.append(f'%{q}%')
        
        if sort_by and sort_by in allowed_sort_fields:
            query += f' ORDER BY {sort_by}'
            if sort_order and sort_order in allowed_sort_orders:
                query += f' {sort_order.upper()}'
        


        offset = (page - 1) * limit
        query += ' LIMIT ? OFFSET ?'
        parameters.append(limit)
        parameters.append(offset)



        cursor.execute(query, parameters)
        movies = cursor.fetchall()
        db.close()
        
        
        data=[dict(movie) for movie in movies]
        
        return jsonify({
            "success": True,
            "message": "Movies retrieved successfully",
            "data": data,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "request_id": str(uuid4())
            }
        })


@app.route('/api/v1/movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    if request.method == 'GET':
        db = get_db()
        cursor = db.cursor()
        query = 'SELECT * FROM movies WHERE id = ?'
        cursor.execute(query, (movie_id,))
        movie = cursor.fetchone()
        db.close()

        if movie:
            return jsonify({
                "success": True,
                "message": "Movie retrieved successfully",
                "data": dict(movie),
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "Movie not found",
                "error": {
                    "code": "NOT_FOUND",
                    "details": f"No movie found with ID {movie_id}"
                },
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            }), 404

@app.route('/api/v1/movies/<movie_id>', methods=['PATCH'])
def update_movie(movie_id):
    if request.method == 'PUT':
        data = request.get_json()

        if data is None:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Validate that the movie exists
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
        existing_movie = cursor.fetchone()

        if not existing_movie:
            db.close()
            return jsonify({
                "success": False,
                "message": "Movie not found",
                "error": {
                    "code": "MOVIE_NOT_FOUND",
                    "details": f"No movie found with ID {movie_id}"
                },
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            }), 404
        
        # Perform validation on input fields (similar to add_movie)
        errors=[]
        title = data.get('title')
        genre = data.get('genre')
        release_year = data.get('release_year')
        status = data.get('status')
        allowed_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Romance', 'Thriller', 'Documentary', 'Animation', 'Adventure']
        date_watched = existing_movie['date_watched']
       
        if title is not None:
            if len(title.strip()) == 0:
                errors.append({"field": "title", "message": "Title cannot be empty."})
            elif len(title.strip()) > 255:
                errors.append({"field": "title", "message": "Title cannot exceed 255 characters."})

        if release_year is not None:
            current_year = datetime.now().year
            if not isinstance(release_year, int):
                errors.append({"field": "release_year", "message": "Release year must be an integer."})     
            elif release_year < 1888:
                errors.append({"field": "release_year", "message": "Release year must be 1888 or later."})
            elif release_year > current_year:
                errors.append({"field": "release_year", "message": f'Release year cannot be in the future (must be {current_year} or earlier).'})
        
        if genre is not None:
            if genre.strip() not in allowed_genres:
                errors.append({"field": "genre", "message": f'Genre must be from the accepted list: {", ".join(allowed_genres)}'})

        if status is not None:
            if status not in ['unwatched', 'watching', 'watched']:
                errors.append({"field": "status", "message": f'Status must be one of: unwatched, watching, watched.'})
                
        current_year = datetime.now().year
        if not release_year:
            errors.append({"field": "release_year", "message": "Release year is required."})
        elif not isinstance(release_year, int):
            errors.append({"field": "release_year", "message": "Release year must be an integer."})     
        elif release_year < 1888:
            errors.append({"field": "release_year", "message": "Release year must be 1888 or later."})
        elif release_year > current_year:
            errors.append({"field": "release_year", "message": f'Release year cannot be in the future (must be {current_year} or earlier).'})
        
        


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
            }), 422
        else:
            if status == 'watched':
                    data['date_watched'] = datetime.now().isoformat()
            elif status != 'watched':
                data['date_watched'] = None
            
            if status == 'unwatched':
                    rating = None
        
            insert_query = '''UPDATE movies SET title = ?, genre = ?, release_year = ?, status = ?, rating = ?, description = ?, director = ?, runtime_minutes = ?, poster_url = ?, priority = ?, notes = ?, date_watched = ? WHERE id = ?'''
            db = get_db()
            cur = db.cursor()
            cur.execute(insert_query, (title.strip() if title else existing_movie['title'], genre.strip() if genre else existing_movie['genre'], release_year if release_year is not None else existing_movie['release_year'], status if status else existing_movie['status'], rating if rating is not None else existing_movie['rating'], description if description else existing_movie['description'], director if director else existing_movie['director'], runtime_minutes if runtime_minutes is not None else existing_movie['runtime_minutes'], poster_url if poster_url else existing_movie['poster_url'], priority if priority else existing_movie['priority'], notes if notes else existing_movie['notes'], date_watched, movie_id))
            db.commit()
            db.close()
            data={
                    "id": movie_id,
                    "title": title if title else existing_movie['title'],
                    "genre": genre if genre else existing_movie['genre'],
                    "release_year": release_year if release_year is not None else existing_movie['release_year'],
                    "status": status if status else existing_movie['status'],
                    "rating": rating if rating is not None else existing_movie['rating'],
                    "date_added": existing_movie['date_added'],    
                    "director": director if director else existing_movie['director'],    
                    "runtime_minutes": runtime_minutes if runtime_minutes is not None else existing_movie['runtime_minutes'],
                    "poster_url": poster_url if poster_url else existing_movie['poster_url'],
                    "priority": priority if priority else existing_movie['priority'],
                    "notes": notes if notes else existing_movie['notes']
                }

            return jsonify({
                "success": True,
                "message": "Movie updated successfully",
                "data": data,
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            }), 200
        
# endpoint to put
@app.route('/api/v1/movies/<movie_id>', methods=['PUT'])
def replace_movie(movie_id):
    if request.method == 'PUT':
        data = request.get_json()

        if data is None:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Validate that the movie exists
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
        existing_movie = cursor.fetchone()

        if not existing_movie:
            db.close()
            return jsonify({
                "success": False,
                "message": "Movie not found",
                "error": {
                    "code": "MOVIE_NOT_FOUND",
                    "details": f"No movie found with ID {movie_id}"
                },
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            }), 404
        
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
            }), 422
        else:
            insert_query = '''UPDATE movies SET title = ?, genre = ?, release_year = ?, status = ?, rating = ?, description = ?, director = ?, runtime_minutes = ?, poster_url = ?, priority = ?, notes = ?, date_watched = ? WHERE id = ?'''
            db = get_db()
            cursor.execute(insert_query, (title.strip(), genre.strip(), release_year, status, rating, description, director, runtime_minutes, poster_url, priority, notes, date_watched, movie_id))
            db.commit()
            db.close()
            return jsonify({
                "success": True,
                "message": "Movie updated successfully",
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
            }), 200


@app.route('/api/v1/movies/<movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    if request.method == 'DELETE':
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
        existing_movie = cursor.fetchone()

        if not existing_movie:
            db.close()
            return jsonify({
                "success": False,
                "message": "Movie not found",
                "error": {
                    "code": "MOVIE_NOT_FOUND",
                    "details": f"No movie found with ID {movie_id}"
                },
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            }), 404
        
        cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
        db.commit()
        db.close()

        return jsonify({
            "success": True,
            "message": "Movie deleted successfully",
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "request_id": str(uuid4())
            }
        }), 200

# Update Movie Status
@app.route('/api/v1/movies/<movie_id>/status', methods=['PATCH'])
def update_movie_status(movie_id):
    if request.method == 'PATCH':
        data = request.get_json()

        if data is None:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        new_status = data.get('status')
        if new_status not in ['unwatched', 'watching', 'watched']:
            return jsonify({
                "success": False,
                "message": "Validation failed",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "details": [{"field": "status", "message": f'Status must be one of: unwatched, watching, watched.'}]        
                },
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            }), 422
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
        existing_movie = cursor.fetchone()

        if not existing_movie:
            db.close()
            return jsonify({
                "success": False,
                "message": "Movie not found",
                "error": {
                    "code": "MOVIE_NOT_FOUND",
                    "details": f"No movie found with ID {movie_id}"
                },
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid4())
                }
            }), 404
        
        date_watched = datetime.now().isoformat() if new_status == 'watched' else None
        rating = None if new_status == 'unwatched' else existing_movie['rating']

        cursor.execute('UPDATE movies SET status = ?, date_watched = ?, rating = ? WHERE id = ?', (new_status, date_watched, rating, movie_id))
        db.commit()
        db.close()

        return jsonify({
            "success": True,
            "message": f"Movie status updated to {new_status}",
            "data": {
                "id": movie_id,
                "status": new_status,
                "date_watched": date_watched,
                "rating": rating
            },
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "request_id": str(uuid4())
            }
        }), 200
    
# app health
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    if request.method == "GET":
        pass