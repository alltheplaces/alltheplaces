
## Postal code data

Postal code data can be very useful for driving store locator query
interfaces which require discrete area parameters. These could be
postal codes or lat/lon.

There are various open data releases of postal code data. Available
here:

**uszips.csv** "BASIC" download from [simplemaps](https://simplemaps.com/data/us-zips)

**outward_gb.json** download from [uk-postcodes](https://github.com/gibbs/uk-postcodes)

The data files should not be used directly but rather accessed
using [library access methods](../../geo.py)
that abstract the underlying differences  and allow easy replacement
with different data set providers.
