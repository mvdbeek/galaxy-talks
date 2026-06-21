# Galaxy talks — build, preview, deploy
#   make            build every deck + the root landing page (index.html)
#   make serve      live-preview a deck in the browser (default DECK=udt)
#   make deploy     build, commit tracked changes (MSG="..."), push -> Pages redeploys
#   make clean      remove Python caches

DECK ?= udt
MSG  ?= Update slides

.PHONY: all serve deploy clean

all:
	./build_all.sh

serve:
	cd $(DECK) && python3 serve.py

deploy: all
	git commit -am "$(MSG)"
	git push

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
