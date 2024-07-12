#!/bin/bash

# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs tmp-data-downloaded-by-hand/siconc_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc
# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs tmp-data-downloaded-by-hand-broken/solarforcing-ref-mon_input4MIPs_solar_CMIP_SOLARIS-HEPPA-4-1_gn_18500101-20231231.nc
# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs \
# 	tmp-data-downloaded-by-hand-broken/H2-em-biomassburning_input4MIPs_emissions_CMIP_DRES-CMIP-BB4CMIP6+-1-0_gn_190001-202212.nc

python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs \
	tmp-data-downloaded-by-hand-broken/CO2-em-anthro_input4MIPs_emissions_CMIP_CEDS-2024-06-04_gn_195001-199912.nc

# # My re-written files
# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs \
# 	tmp-data-iris/input4MIPs/CMIP6Plus/CMIP/CR/CR-CMIP-0-2-0/atmos/mon/mole-fraction-of-carbon-dioxide-in-air/gmnhsh/v20240711/mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_CMIP_CR-CMIP-0-2-0_gmnhsh_175001-202212.nc
#
# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs \
# 	tmp-data-iris/input4MIPs/CMIP6Plus/CMIP/CR/CR-CMIP-0-2-0/atmos/yr/mole-fraction-of-carbon-dioxide-in-air/gmnhsh/v20240711/mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_CMIP_CR-CMIP-0-2-0_gmnhsh_1750-2022.nc
#
# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs \
# 	tmp-data-iris/input4MIPs/CMIP6Plus/CMIP/SOLARIS-HEPPA/SOLARIS-HEPPA-CMIP-4-1/atmos/mon/solar-irradiance/gn/v20240711/solar-irradiance_input4MIPs_solar_CMIP_SOLARIS-HEPPA-CMIP-4-1_gn_185001-202312.nc
#
# python src/input4mips_validation/cli/__init__.py validate-file --cv-source ../input4MIPs_CVs/CVs \
# 	tmp-data-iris/input4MIPs/CMIP6Plus/CMIP/PCMDI/PCMDI-AMIP-1-1-9/seaIce/mon/siconc/gn/v20240711/siconc_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc
