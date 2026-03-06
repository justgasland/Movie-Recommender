"""Utility script to initialize and populate the movie database with
random test data.  The module is intentionally standalone so you can
run it independently of the Flask application when you need to stress
and exercise validation and query logic.

Usage examples:

    # make sure dependencies are installed (faker is used)
    pip install faker

    # create or reset the database and insert 1 000 random movies
    python update.py --count 1000

    # generate a JSON file with 500 entries (does not touch the DB)
    python update.py --count 500 --export data.json

The generated records honour the schema constraints defined in
`app.py` and will hit edge cases such as the longest titles, invalid
URLs, future release years, etc., as commanded by the `--include-invalid`
flag.
"""

import argparse
import json
import random
import sqlite3
from datetime import datetime
from uuid import uuid4

from faker import Faker


database = "movies.db"


# copy helpers from app.py so the script can operate on the same schema

ALLOWED_GENRES = [
    "Action",
    "Comedy",
    "Drama",
    "Horror",
    "Sci-Fi",
    "Romance",
    "Thriller",
    "Documentary",
    "Animation",
    "Adventure",
]

ALLOWED_STATUSES = ["unwatched", "watching", "watched"]
ALLOWED_PRIORITIES = ["high", "normal", "low"]


def get_db():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the movies table if it does not already exist.  This is the
same schema used by the Flask application."""
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


_fake = Faker()


def generate_movie(include_invalid: bool = False) -> dict:
    """Return a single random movie dictionary.  If ``include_invalid`` is
True, occasionally produce values that will fail the Flask validation so
you can verify error handling."""

    title = _fake.sentence(nb_words=random.randint(1, 6)).rstrip(".")
    if include_invalid and random.random() < 0.05:
        # make an excessively long title or an empty one
        title = "" if random.choice((True, False)) else "A" * 300

    genre = random.choice(ALLOWED_GENRES)
    if include_invalid and random.random() < 0.02:
        genre = "InvalidGenre"

    current_year = datetime.now().year
    release_year = random.randint(1888, current_year)
    if include_invalid and random.random() < 0.03:
        release_year = current_year + 5  # future year

    status = random.choice(ALLOWED_STATUSES)
    rating = None
    if status == "watched":
        rating = random.randint(1, 5)
        if include_invalid and random.random() < 0.02:
            rating = 10  # out of range
    else:
        if include_invalid and random.random() < 0.02:
            rating = "bad"

    director = _fake.name()
    runtime_minutes = random.randint(60, 180)
    if include_invalid and random.random() < 0.02:
        runtime_minutes = -5

    poster_url = _fake.image_url()
    if include_invalid and random.random() < 0.02:
        poster_url = "not a url"

    priority = random.choice(ALLOWED_PRIORITIES)
    notes = _fake.text(max_nb_chars=200) if random.random() < 0.5 else None
    description = _fake.text(max_nb_chars=500) if random.random() < 0.5 else None

    cast = None
    if random.random() < 0.4:
        count = random.randint(1, 10)
        cast = [_fake.name() for _ in range(count)]
        if include_invalid and random.random() < 0.02:
            cast.append(123)  # non-string entry

    return {
        "title": title,
        "genre": genre,
        "release_year": release_year,
        "status": status,
        "rating": rating,
        "director": director,
        "runtime_minutes": runtime_minutes,
        "poster_url": poster_url,
        "priority": priority,
        "notes": notes,
        "description": description,
        "cast": cast,
    }


def generate_test_movies(count: int, include_invalid: bool = False) -> list:
    """Generate a list of ``count`` movie dictionaries."""
    return [generate_movie(include_invalid) for _ in range(count)]


def insert_movies(movies: list):
    """Insert a list of movie dicts into the database.  Duplicate titles/years
are skipped (SQLite UNIQUE constraint)."""
    db = get_db()
    cursor = db.cursor()
    insert_query = '''INSERT OR IGNORE INTO movies
    (id, title, genre, release_year, status, rating, description, director,
     runtime_minutes, poster_url, priority, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    for m in movies:
        cursor.execute(
            insert_query,
            (
                str(uuid4()),
                m.get("title"),
                m.get("genre"),
                m.get("release_year"),
                m.get("status"),
                m.get("rating"),
                m.get("description"),
                m.get("director"),
                m.get("runtime_minutes"),
                m.get("poster_url"),
                m.get("priority"),
                m.get("notes"),
            ),
        )
    db.commit()
    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and insert test movies.")
    parser.add_argument(
        "--count", "-c", type=int, default=100, help="How many movies to create"
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Insert some records with invalid values for testing validation",
    )
    parser.add_argument(
        "--export",
        help="Write the generated records to the given JSON file instead of
inserting into the database",
    )
    args = parser.parse_args()

    # always start with a fresh schema
    init_db()

    movies = generate_test_movies(args.count, include_invalid=args.include_invalid)
    if args.export:
        with open(args.export, "w", encoding="utf-8") as fp:
            json.dump(movies, fp, indent=2)
        print(f"Wrote {len(movies)} movies to {args.export}")
    else:
        insert_movies(movies)
        print(f"Inserted {len(movies)} movies into {database}")
