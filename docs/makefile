SHELL=/bin/bash

serve:
	cd .. && mkdocs serve

images:
	cd img && for I in *.png; do cwebp -lossless $${I} -o $${I//png/webp}; done
	rm img/*.png
