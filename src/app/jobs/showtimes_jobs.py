# docker exec -it movie-booking-be-app-1 poetry run python src/app/jobs/showtimes_jobs.py

import sys, os, random
from datetime import datetime, timedelta, timezone

sys.path.append('/app')

from wsgi import app
from src.app import db
from src.app.models.showtimes import Showtime
from src.app.models.movie import Movie
from src.app.models.auditorium import Auditorium

def delete_old_showtimes() -> None:
    '''Deletes showtimes that have already passed.'''
    now = datetime.now(timezone.utc)
    old_showtimes = Showtime.query.filter(Showtime.starts_at < now).all()
    
    for showtime in old_showtimes:
        db.session.delete(showtime)
    
    db.session.commit()
    print(f"Deleted {len(old_showtimes)} old showtimes.")


def create_new_showtimes(showtimes: int, days_ahead: int = 7) -> None:
    '''
    Creates n number of showtimes a week from the current date.
    '''
    movie_count = Movie.query.count()
    half_movies = Movie.query.limit(movie_count // 2).all()
    all_auditoriums = Auditorium.query.all()

    if not half_movies or not all_auditoriums:
        print("Missing movies or auditoriums to seed showtimes.")
        return

    created_count = 0
    target_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    
    prices = {
        "child": 800,
        "adult": 1200,
        "senior": 1000
    }

    for _ in range(showtimes):
        movie = random.choice(half_movies)
        auditorium = random.choice(all_auditoriums)
        
        random_hour = random.randint(10, 22)
        start_time = target_date.replace(hour=random_hour, minute=0, second=0, microsecond=0)

        exists = Showtime.query.filter_by(
            auditorium_id=auditorium.auditorium_id, 
            starts_at=start_time
        ).first()

        if not exists:
            new_showtime = Showtime(
                movie_id=movie.movie_id,
                auditorium_id=auditorium.auditorium_id,
                starts_at=start_time,
                child_price_cents=prices["child"],
                adult_price_cents=prices["adult"],
                senior_price_cents=prices["senior"]
            )
            db.session.add(new_showtime)
            created_count += 1

    db.session.commit()
    print(f"Created {created_count} new showtimes for {target_date.date()}.")


def initial_seed(days: int) -> None:
    '''
    Inital seed, seeds random showtimes from current day - 7 days in the future.
    '''
    for i in range(days):
        create_new_showtimes(2, days_ahead=i)
    return

if __name__ == "__main__":
    with app.app_context():
        delete_old_showtimes()
        daily_limit = int(os.getenv("DAILY_SHOWTIMES", 2))
        create_new_showtimes(daily_limit)
        # initial_seed(7)