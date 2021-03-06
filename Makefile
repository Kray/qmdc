
SRCS = src/qmdc.c

PYSRCS= src/head.py \
	src/connection.py \
	src/dbus.py \
	src/mainview.py \
	src/playqueue.py \
	src/profileedit.py \
	src/profileselector.py \
	src/qmdc.py \
	src/search.py \
	src/topbar.py \
	src/trackinfo.py \
	src/tracklistview.py \
	src/transcodingoptions.py \
	src/tail.py

CFLAGS += -g -Wall -Wextra $(shell pkg-config python-2.7 --cflags)
LIBS = -lpthread $(shell pkg-config python-2.7 --libs) -lao -lavutil -lavcodec

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
