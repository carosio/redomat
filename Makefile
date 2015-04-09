DESTDIR ?= /usr/local
BIN_DIR= $(DESTDIR)/bin
LIBEXEC_DIR= $(DESTDIR)/libexec/redomat

dist/redomat/redomat: venv_and_deps redomat.py
	./venv/bin/pyinstaller -y redomat.py

venv:
	virtualenv $@

venv_and_deps: venv
	./venv/bin/pip install --download-cache=vendor -r requirements.txt

install: dist/redomat/
	install -v -d $(LIBEXEC_DIR)
	install -v -d $(BIN_DIR)
	( cd $< && find . -type f -exec install -v -D -t $(LIBEXEC_DIR) '{}' ';' )
	ln -fs $(LIBEXEC_DIR)/redomat $(BIN_DIR)/redomat

clean:
	rm -fr venv dist


.PHONY: venv_and_deps clean install
