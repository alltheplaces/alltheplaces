## Categories

For the most part we can automatically get the category from [NSI](https://nsi.guide/) after a successful match with `brand:wikidata`.
However, this is not always possible.
When it isn't automatically applied, it should be explicitly set in the spider, for this we have the helper function `apply_category`,
which takes a category from the `Categories` enum and the POI.

The `Categories` enum can be extended with [OSM categories](https://wiki.openstreetmap.org/wiki/Map_features), this
should be the "top level" tag, additional attributes can be added with `apply_yes_no` or directly to `extras`.
