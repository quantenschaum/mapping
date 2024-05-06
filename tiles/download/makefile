index.html:

%.html: %.md $(wildcard *)
	./times.py $< >x$<
	pandoc -s x$< -o $@ --metadata title="Download"
	rm x$<
