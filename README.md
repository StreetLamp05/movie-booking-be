# Movie Booking Backend (Flask + PostgreSQL)
FLask API with SQLAlchemy, Alembic (Flask-migrate), CORS, and a wsgi endpoint. 
Runs in a docker container w/ postgres.

### quick start

``` shell
git clone https://github.com/StreetLamp05/movie-booking-be.git
cd movie-booking-be
```

``` shell
cp .env.example .env.development
```

``` shell
cat > .env.development << 'EOF'
FLASK_ENV=development
SECRET_KEY=dev-change-me

# Postgres (matches docker-compose)
DB_HOST=db
DB_PORT=5432
DB_USER=app_user
DB_PASSWORD=app_pass
DB_NAME=app_dev

SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://app_user:app_pass@db:5432/app_dev

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
```

```shell
docker compose up --build -d

```

``` shell
# init migrations (do once)
docker compose exec app poetry run flask db init
docker compose exec app poetry run flask db migrate -m "init"
docker compose exec app poetry run flask db upgrade
```

``` shell
# test
curl http://localhost:5000/api/v1/health

# Seed a test user (creates 1 row) (not reflective of final db, just testing)
curl -X POST http://localhost:5000/api/v1/seed
```


### important info:
#### Runtime Envs:
Dev (default): entrypoint.sh waits for Postgres, runs flask db upgrade, then starts the Flask dev server on :5000 with --debug.
For prod: switch to Gunicorn in the entrypoint.sh

## Alembic Commands
#### create a new migration (after model changes)
docker compose exec app poetry run flask db migrate -m "add movies table"

#### apply latest migrations
docker compose exec app poetry run flask db upgrade

#### show current DB head
docker compose exec app poetry run flask db current

don't run flask db init if migrations/ dir exists

