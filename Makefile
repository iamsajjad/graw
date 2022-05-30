
CC=clang
CFLAGS=-g -Wall -Wextra -ggdb
LIBS=-luv -lcurl
OBJS=graw.o parson.o
PROJ=graw

.PHONY: all
%.o: %.c
	$(CC) -c -o $@ $< $(CFLAGS)

graw: $(OBJS)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

test:graw
	echo "need test here !"

.PHONY: clean
clean:
	$(RM) $(OBJS) $(PROJ)
