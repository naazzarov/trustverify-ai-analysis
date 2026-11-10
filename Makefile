.PHONY: test data benchmark demo pilot figures
test:
	python3 -m unittest discover -s tests -v
data:
	python3 -m trustverify.cli generate
benchmark:
	python3 -m trustverify.cli benchmark
demo:
	python3 -m trustverify.server
pilot:
	python3 -m trustverify.live
figures:
	python3 scripts/make_figures.py
