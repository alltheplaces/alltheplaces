
## Postal code data

Postal code data can be very useful for driving store locator query
interfaces which require discrete area parameters. These could be
postal codes or lat/lon.

There are various open data releases of postal code data. Available
here:

- **uszips.csv** "BASIC" download from [simplemaps](https://simplemaps.com/data/us-zips)
- **outward_gb.json** download from [uk-postcodes](https://github.com/gibbs/uk-postcodes)
- **japostcodes.zip** download from [日本郵便 (Japan Post)](https://www.post.japanpost.jp/service/search/zipcode/download/utf-zip.html).
  - The stable URL `https://www.post.japanpost.jp/service/search/zipcode/download/utf/zip/utf_ken_all.zip`
always serves the latest nationwide release (refreshed monthly). It is the one record per line, UTF-8 format containing the JIS
municipality code, postcode, and prefecture/city/town names in kanji and kana.
  - License: Japan Post states that they do not assert copyright on this data it can be freely re-distributed.

The data files should not be used directly but rather accessed
using [library access methods](../../geo.py)
that abstract the underlying differences  and allow easy replacement
with different data set providers.
