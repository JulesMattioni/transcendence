# ─────────────────────────────────────────────────────────────
# SecureVault — Makefile
# Shortcuts around Docker Compose.
# ─────────────────────────────────────────────────────────────

COMPOSE := docker compose

.PHONY: run up down stop build logs ps re clean fclean help

## run   : build + start the whole stack (foreground)
run:
	$(COMPOSE) up --build

## up    : start the stack in the background (detached)
up:
	$(COMPOSE) up --build -d

## down  : stop and remove containers + networks
down:
	$(COMPOSE) down

## stop  : stop containers without removing them
stop:
	$(COMPOSE) stop

## build : (re)build the images without starting
build:
	$(COMPOSE) build

## logs  : follow the logs of all services
logs:
	$(COMPOSE) logs -f

## ps    : list the state of the services
ps:
	$(COMPOSE) ps

## re    : restart cleanly (down then run)
re: down run

## clean : project containers + images + orphans (KEEPS volumes)
clean:
	$(COMPOSE) down --rmi local --remove-orphans

## fclean: everything, volumes INCLUDED (wipes the Postgres database)
fclean:
	$(COMPOSE) down --rmi local --volumes --remove-orphans

## help  : list the available targets
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //'
