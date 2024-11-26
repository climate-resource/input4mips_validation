"""
Grab the CF standard name table

Workaround for https://github.com/readthedocs/readthedocs.org/issues/11763
while we wait for https://github.com/xarray-contrib/cf-xarray/pull/547.
"""

import pooch

DOWNLOADER = pooch.HTTPDownloader(
    # https://github.com/readthedocs/readthedocs.org/issues/11763
    headers={"User-Agent": "input4mips-validation"}
)
pooch.retrieve(
    "https://raw.githubusercontent.com/cf-convention/cf-convention.github.io/master/Data/cf-standard-names/current/src/cf-standard-name-table.xml",
    known_hash=None,
    downloader=DOWNLOADER,
)
