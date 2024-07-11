#!/bin/bash

# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs tmp-data-downloaded-by-hand-broken/solarforcing-ref-mon_input4MIPs_solar_CMIP_SOLARIS-HEPPA-4-1_gn_18500101-20231231.nc
python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs tmp-data-downloaded-by-hand/siconc_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc
# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs tmp-data-iris/input4MIPs/CMIP6Plus/CMIP/CR/CR-CMIP-0-2-0/atmos/yr/mole-fraction-of-carbon-dioxide-in-air/gmnhsh/0-2-0/mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_CMIP_CR-CMIP-0-2-0_gmnhsh_1750-2022.nc
