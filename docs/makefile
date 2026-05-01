SHELL=/bin/bash

serve:
	cd .. && mkdocs serve

images:
	cd img && for I in *.png; do cwebp -lossless $${I} -o $${I//png/webp}; done
	rm img/*.png

install:
	pip install --break-system-packages mkdocs mkdocs-material mkdocs-i18n mkdocs-static-i18n mkdocs-git-revision-date-localized-plugin
