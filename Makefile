SRCS = qmdc.c

RUN_IN_PLACE ?= 0

CFLAGS += -g -Wall -Wextra $(shell python2-config --cflags)
LIBS = $(shell python2-config --libs) -lao -lavcodec

PREFIX ?= /usr/local

qmdc: $(SRCS)
	$(CC) $(CFLAGS) $(SRCS) -o qmdc $(LIBS)

install: qmdc
	install -d $(PREFIX)/bin/
	install -m 0755 qmdc.py $(PREFIX)/bin/
	install -m 0755 qmdc-ctrl $(PREFIX)/bin/
