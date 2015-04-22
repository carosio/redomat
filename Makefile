VIRTUALENV_VERSION = 12.1.1

DESTDIR ?= /usr/local
BIN_DIR= $(DESTDIR)/bin
LIBEXEC_DIR= $(DESTDIR)/libexec/redomat

dist/redomat/redomat: venv_and_deps redomat.py
	./venv/bin/pyinstaller -y redomat.py

venv_and_deps: venv
	./venv/bin/pip install --cache-dir=vendor -r requirements.txt


vendor/virtualenv-$(VIRTUALENV_VERSION).tar.gz : vendor
	wget -O $@ https://github.com/pypa/virtualenv/archive/$(VIRTUALENV_VERSION).tar.gz

install: dist/redomat/
	install -v -d $(LIBEXEC_DIR)
	install -v -d $(BIN_DIR)
	( cd $< && find . -type f -exec install -v -D -t $(LIBEXEC_DIR) '{}' ';' )
	ln -fs $(LIBEXEC_DIR)/redomat $(BIN_DIR)/redomat

clean:
	rm -fr venv dist tmp

venv: tmp/virtualenv-$(VIRTUALENV_VERSION)/virtualenv.py
	python tmp/virtualenv-$(VIRTUALENV_VERSION)/virtualenv.py $@

tmp/virtualenv-$(VIRTUALENV_VERSION)/virtualenv.py: tmp vendor/virtualenv-$(VIRTUALENV_VERSION).tar.gz
	cd tmp && tar xf ../vendor/virtualenv-$(VIRTUALENV_VERSION).tar.gz

vendor:
	mkdir -p $@

tmp:
	mkdir -p $@



.PHONY: venv_and_deps clean install
