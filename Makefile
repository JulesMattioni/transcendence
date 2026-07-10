# ─────────────────────────────────────────────────────────────
# SecureVault — Makefile
# Shortcuts around Docker Compose.
# ─────────────────────────────────────────────────────────────

# Active Compose profile (dev by default). Override with: make PROFILE=prod ...
PROFILE ?= dev
COMPOSE := docker compose --profile $(PROFILE)

CERT_DIR := gateway/certs
CRS_DIR := gateway/crs
CRS_REPO := https://github.com/coreruleset/coreruleset.git

.PHONY: run prod up down stop build logs ps re certs crs clean fclean help

## certs : generate self-signed TLS cert for the gateway (skips if present)
certs:
	@if [ -f $(CERT_DIR)/server.crt ] && [ -f $(CERT_DIR)/server.key ]; then \
		echo "certs already present in $(CERT_DIR)/ — skipping"; \
	else \
		mkdir -p $(CERT_DIR); \
		openssl req -x509 -newkey rsa:2048 -nodes \
			-keyout $(CERT_DIR)/server.key \
			-out $(CERT_DIR)/server.crt \
			-days 365 -subj "/CN=localhost"; \
		echo "generated $(CERT_DIR)/server.crt and server.key"; \
	fi

## crs   : clone OWASP Core Rule Set for the gateway WAF (skips if present)
crs:
	@if [ -d $(CRS_DIR)/rules ] && [ -f $(CRS_DIR)/crs-setup.conf.example ]; then \
		echo "CRS already present in $(CRS_DIR)/ — skipping"; \
	else \
		rm -rf $(CRS_DIR); \
		git clone --depth 1 $(CRS_REPO) $(CRS_DIR); \
		echo "cloned CRS into $(CRS_DIR)/"; \
	fi

## run   : build + start the whole stack in dev profile (foreground)
run: certs crs
	$(COMPOSE) up --build

## prod  : build + start the whole stack in prod profile (foreground)
prod:
	$(MAKE) run PROFILE=prod

## up    : start the stack in the background (detached)
up: certs crs
	$(COMPOSE) up --build -d

## down  : stop and remove containers + networks
down:
	$(COMPOSE) down

## stop  : stop containers without removing them
stop:
	$(COMPOSE) stop

## build : (re)build the images without starting
build: certs crs
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
