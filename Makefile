.PHONY: test data benchmark demo pilot figures check public-data report
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
	python3 scripts/study_artifacts.py

check:
	python3 scripts/check_results.py
	python3 scripts/check_study.py
public-data:
	python3 -m trustverify.public_data
report:
	cd paper && tectonic -X compile main.tex
