.PHONY: install extract summarize discover test
install:
	pip install -e .
extract:
	ati extract
summarize:
	ati summarize
discover:
	ati discover
test:
	pytest -q
