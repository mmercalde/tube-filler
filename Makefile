# TUBE-FILLER
PY ?= $(HOME)/cadenv/bin/python

.PHONY: all calcs cad assembly clash clean
all: cad

calcs:                 ## design summary + acceptance asserts
	$(PY) calcs/pump_calcs.py

cad: calcs             ## everything: STEP/STL/DXF/SVG/PDF, assembly, BOM, manifest
	$(PY) cad/build_all.py

assembly:              ## machine_assembly.step + assembly_iso.svg only
	$(PY) -c "import sys;sys.path.insert(0,'cad');import assembly;print(*assembly.export(),sep='\n')"

clash:                 ## interpenetration report, nothing exported
	$(PY) -c "import sys;sys.path.insert(0,'cad');import assembly;\
c=assembly.clashes();print(f'{len(c)} unintended clashes');\
[print(f'  {v:10.0f} mm3  {a} <-> {b}') for a,b,v in c]"

clean:
	rm -rf out/*
