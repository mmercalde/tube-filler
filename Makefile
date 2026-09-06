# TUBE-FILLER
PY ?= $(HOME)/cadenv/bin/python

.PHONY: all calcs cad clean
all: cad

calcs:                 ## design summary + acceptance asserts
	$(PY) calcs/pump_calcs.py

cad: calcs             ## every STEP/STL/DXF/SVG/PDF + BOM.md + design_summary.txt
	$(PY) cad/build_all.py

clean:
	rm -rf out/*
