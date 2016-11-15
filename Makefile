SERVER_CONFIG = alwaysdata_kinto/alwaysdata_kinto.ini

VIRTUALENV = virtualenv
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
PYTHON = $(VENV)/bin/python
INSTALL_STAMP = $(VENV)/.install.stamp

.IGNORE: clean distclean maintainer-clean
.PHONY: all install virtualenv tests

OBJECTS = .venv .coverage

help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  install                     install dependencies and prepare environment"
	@echo "  serve                       start the web server on default port (9999)"
	@echo "  clean                       remove *.pyc files and __pycache__ directory"
	@echo "  distclean                   remove *.egg-info files and *.egg, build and dist directories"
	@echo "  maintainer-clean            remove the .tox and the .venv directories"
	@echo "Check the Makefile to know exactly what each target is doing."

all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON) alwaysdata_kinto/setup.py
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -Ue alwaysdata_kinto/
    npm install
	touch $(INSTALL_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

build-requirements:
	$(VIRTUALENV) $(TEMPDIR)
	$(TEMPDIR)/bin/pip install -U pip
	$(TEMPDIR)/bin/pip install -Ue alwaysdata_kinto
	$(TEMPDIR)/bin/pip freeze > requirements.txt

serve: install
	$(VENV)/bin/pserve alwaysdata_kinto/alwaysdata_kinto.ini --reload

worker: install
	$(VENV)/bin/alwaysdata-kinto-worker --ini alwaysdata_kinto/alwaysdata_kinto.ini

web:
	npm run live

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d | xargs rm -fr

distclean: clean
	rm -fr *.egg *.egg-info/ dist/ build/

maintainer-clean: distclean
	rm -fr .venv/ .tox/
