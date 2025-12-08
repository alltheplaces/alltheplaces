## Categories

For the most part we can automatically get the category from [NSI](https://nsi.guide/) after a successful match with `brand:wikidata`.
However, this is not always possible.
When it isn't automatically applied, it should be explicitly set in the spider, for this we have the helper function `apply_category`,
which takes a category from the `Categories` enum and the POI.

The `Categories` enum can be extended with [OSM categories](https://wiki.openstreetmap.org/wiki/Map_features), this
should be the "top level" tag, additional attributes can be added with `apply_yes_no` or directly to `extras`.

### Output

We follow [OSM categories](https://wiki.openstreetmap.org/wiki/Map_features), as best we can, however there are times
when we don't know the correct category.
For these we may use [`amenity=yes`](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dyes), you may be able to get some
value from them by clustering them with other data eg collecting `post_office=post_partner` from `czech_post_cz`,
however you probably don't want to put them in a product on their own.
