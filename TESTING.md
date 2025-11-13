# How to run tests.
## To run isolated tests 
pytest <your/file/path> 

## To run repo-wide test
uv run pytest
or
pytest

# Files created/modified
## Created
locations/commands/genspider.py
locations/commands/sitemap.py
locations/commands/nsi.py
locations/storefinders/treeplotter.py
locations/storefinders/wp_store_locator.py
locations/storefinders/geo_me.py

## Modified
pyproject.toml
uv.lock

# Description of custom exceptions and their use cases

# Test coverage summary
                                                                                                          Stmts   Miss  Cover
locations/commands/genspider.py                                                                             64      0   100%

locations/commands/sitemap.py                                                                               75      8    89%

locations/commands/nsi.py                                                                                   92      0   100%

locations/storefinders/wp_store_locator.py                                                                  101     25    75%

locations/storefinders/geo_me.py                                                                            67      1    99%

locations/storefinders/treeplotter.py                                                                       131    102    22%

TOTAL                                                                                                       110796  55654    50%


# Any known issues or limitations
## Two files needed updating when running repo wide test. 
locations/data/nsi-wikidata.json 
tests/data/londis.html

