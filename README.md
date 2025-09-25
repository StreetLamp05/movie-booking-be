quick start

git clone https://github.com/StreetLamp05/movie-booking-be.git
cd movie-booking-be

cp .env.example .env.development

docker compose up --build -d

# init migrations (do once)
docker compose exec app poetry run flask db init
docker compose exec app poetry run flask db migrate -m "init"
docker compose exec app poetry run flask db upgrade

# test
curl http://localhost:5000/health
curl -X POST http://localhost:5000/seed
