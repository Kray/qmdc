
SRCS = src/qmdc.c

PYSRCS= src/head.py \
	src/connection.py \
	src/tracklistview.py \
	src/playqueue.py \
	src/search.py \
	src/topbar.py \
	src/mainview.py \
	src/connectdialog.py \
	src/dbus.py \
	src/qmdc.py \
	src/main.py

CFLAGS += -g -Wall -Wextra $(shell pkg-config python-2.7 --cflags)
LIBS = $(shell pkg-config python-2.7 --libs) -lao -lavcodec

RUN_IN_PLACE ?= 0

PREFIX ?= /usr/local

qmdc: $(SRCS) $(PYSRCS)
	$(CC) $(CFLAGS) $(SRCS) -o qmdc $(LIBS)
	cat pyheader.txt $(PYSRCS) > qmdc.py

install: qmdc
	install -d $(PREFIX)/bin/
	install -m 0755 qmdc $(PREFIX)/bin/
	install -m 0755 qmdc.py $(PREFIX)/bin/
	install -m 0755 qmdc-ctrl $(PREFIX)/bin/
