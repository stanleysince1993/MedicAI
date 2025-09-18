ENV_FILE=backend/.env

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

migrate:
	docker compose exec api alembic upgrade head

logs:
	docker compose logs -f api

dev:
	uvicorn backend.main:app --reload

test:
	pytest -q
