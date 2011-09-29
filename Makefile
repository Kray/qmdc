SRCS = qmdc.c

RUN_IN_PLACE ?= 0

CFLAGS += -g -Wall -Wextra $(shell pkg-config python-2.7 --cflags)
LIBS = $(shell pkg-config python-2.7 --libs) -lao -lavcodec

PREFIX ?= /usr/local

qmdc: $(SRCS)
	$(CC) $(CFLAGS) $(SRCS) -o qmdc $(LIBS)

install: qmdc
	install -d $(PREFIX)/bin/
	install -m 0755 qmdc $(PREFIX)/bin/
	install -m 0755 qmdc.py $(PREFIX)/bin/
	install -m 0755 qmdc-ctrl $(PREFIX)/bin/
