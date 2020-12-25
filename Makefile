.PHONY: shell lint test schema

ifeq ($(GIT),)
  GIT := $(HOME)/git
endif

IMAGE := base-python-sql
NAME := aiomysql
MYSQL := mysql

NET := --net test
MOUNT := /opt/git
VOLUMES := -v=$(GIT):$(MOUNT)
WORKING := -w $(MOUNT)/$(NAME)
PYTHONPATH := .
ENV := -e PYTHONPATH=$(PYTHONPATH)

DOCKER := docker run --rm -it $(ENV) $(VOLUMES) $(WORKING) $(NET) $(IMAGE)

shell:
	$(DOCKER) bash

lint:
	$(DOCKER) pylint $(NAME)

test:
	$(DOCKER) pytest

schema:
	$(DOCKER) bash -c "mysql -h $(MYSQL) -v < /opt/git/aiomysql/schema/schema.sql"
