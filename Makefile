SRCS = qmdc.c

RUN_IN_PLACE ?= 0

CFLAGS += -g -Wall -Wextra $(shell python2-config --cflags)
LIBS = $(shell python2-config --libs) -lao -lavcodec

qmdc: $(SRCS)
	$(CC) $(CFLAGS) $(SRCS) -o qmdc $(LIBS)

install: qmdc
	install -m 0755 qmdc $(PREFIX)/bin/
