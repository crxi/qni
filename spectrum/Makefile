PY ?= python3
WEB_IMG := ../web/public/images

.PHONY: svg png pdf all clean web

svg: output/spectrum.svg

output/spectrum.svg: data.yaml render.py
	$(PY) render.py

png: ; $(PY) render.py --format png
pdf: ; $(PY) render.py --format pdf
all: svg png pdf

# Mirror the SVG + 2K PNG into the Astro public/images dir so the
# /spectrum page's download + expand toolbar resolves at build time
# (ZoomModal loads the static SVG; the download button saves the 2K
# PNG). render.py --format png already produces
# a 2x-wide PNG (output_width = 2 × canvas.width) at output/spectrum.png;
# rename it to spectrum_2k.png in the public dir so the page-side URL
# convention stays consistent with the rest of the workspace.
web: all
	mkdir -p $(WEB_IMG)
	cp output/spectrum.svg  $(WEB_IMG)/spectrum.svg
	cp output/spectrum.png  $(WEB_IMG)/spectrum_2k.png

clean:
	rm -f output/spectrum.svg output/spectrum.png output/spectrum.pdf
