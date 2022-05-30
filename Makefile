
CC=clang
CFLAGS=-g -Wall -Wextra
LIBS=-luv -lcurl -lparson
OBJS=graw.o
PROJ=graw

%.o: %.c
	$(CC) -c -o $@ $< $(CFLAGS)

graw: $(OBJS)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

test:graw
	echo "need test here !"
clean:
	$(RM) $(OBJS) $(PROJ)
