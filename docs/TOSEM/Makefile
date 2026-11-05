LATEXMK ?= latexmk
LATEXFLAGS = -pdf -interaction=nonstopmode -halt-on-error

.PHONY: all manuscript preview clean
all: manuscript preview

manuscript:
	$(LATEXMK) $(LATEXFLAGS) main.tex

preview:
	$(LATEXMK) $(LATEXFLAGS) journal-preview.tex

clean:
	$(LATEXMK) -c main.tex journal-preview.tex
