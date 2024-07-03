"""
Test loading of CVs from PCMDI GitHub main
"""
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)

raw_cvs_loader = get_raw_cvs_loader(cv_source="gh:main")
print(raw_cvs_loader)
cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)
print(cvs)
