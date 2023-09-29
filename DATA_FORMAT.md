# All The Places Data Format

The output of the periodic run of all spiders posted on https://www.alltheplaces.xyz/ is a .zip of each spider's output. Each spider produces a single GeoJSON `FeatureCollection` where each `Feature` contains the data for a single scraped item. Along with the GeoJSON output, the collection includes logs and statistics, which can help understand what happened during the spider's run.

## Identifier

Each GeoJSON feature will have an `id` field. The ID is a hash based on the `ref` and `@spider` fields and should be consistent between builds.

Data consumers might use the `id` field to determine if new objects show up or disappear between builds. Occasionally, the authors of spiders will change the spider name or the website we spider will change the identifiers used for the store. In these cases, the ID field in our output will change dramatically. At this time, we don't make an attempt to link the old and new IDs. Also, in some cases a spider author is unable to find a stable identifier for an item and each run will get a unique identifier.

## Geometry

In most cases, the feature will include a `geometry` field following [the GeoJSON spec](https://tools.ietf.org/html/rfc7946#section-3.1). There are some spiders that aren't able to recover a position from the venue's website. In those cases, the geometry is set to `null` and only the properties are included.

Although it's not supported at the time of this writing, we hope to include a geocoding step in the pipeline so that these feature will get a position added.

## Properties

Each GeoJSON feature will have a `properties` object with as many of the following properties as possible, however only `@spider` is guaranteed:

| Name                  | Description |
|-----------------------|---|
| `ref`                 | A unique identifier for this feature inside this spider. The code that generates the output will remove duplicates based on the value of this key.
| `@spider`             | The name of the spider that produced this feature. It is [specified in each spider](https://github.com/alltheplaces/alltheplaces/blob/11d9be56515ef0f6419e001b1950f69d28d4f400/locations/spiders/apple.py#L9), so it isn't necessarily related to the file name of the spider.
| `branch`              | This is often the location specific part of a chain location's name, like the name of the mall or city it is in, without the brand name included.
| `name`                | The name of the feature. Ideally the fascia, However this is often a combination of the brand and the branch.
| **Brand**             | _Information about the brand that operates or owns the venue_
| `brand`               | The brand or chain name of the feature. This will generally be the same for most features outputted by a scraper. Some scrapers will output for companies that own multiple brands, like Duane Reade and Walgreens for the Walgreens scraper.
| `brand:wikidata`      | The [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) [item ID](https://www.wikidata.org/wiki/Help:Items) for the brand of the feature. This is a machine-readable identifier counterpart for the human-readable `brand` above.
| **Address**           | _Information about the address of the venue_
| `addr:full`           | The full address for the venue in one line of text. Usually this follows the format of street, city, province, postcode address. This field might exist instead of the other address-related fields, especially if the spider can't reliably extract the individual parts of the address.
| `addr:housenumber`    | The house number part of the address.
| `addr:street`         | The street name.
| `addr:street_address` | The street address, including street name and house number and/or name.
| `addr:city`           | The city part of the address.
| `addr:state`          | The state or province part of the address.
| `addr:postcode`       | The postcode part of the address.
| `addr:country`        | The country part of the address.
| **Contact**           | _Contact information for the venue_
| `phone`               | The telephone number for the venue. Note that this is usually pulled from a website assuming local visitors, so it probably doesn't include the country code.
| `website`             | The website for the venue. We try to make this a URL specific to the venue and not a generic URL for the brand that is operating the venue.
| `contact:email`       | The email address for the venue. We try to make this an email specific to the venue and not a generic email for the brand that is operating the venue.
| `contact:twitter`     | The twitter account for the venue. We try to make this specific to the venue and not generic for the brand that is operating the venue.
| `contact:facebook`    | The facebook account for the venue. We try to make this specific to the venue and not generic for the brand that is operating the venue.
| **Other**             | _Other information about the venue_
| `opening_hours`       | The opening hours for the venue. When we can, the format for this field follows [OpenStreetMap's `opening_hours` format](https://wiki.openstreetmap.org/wiki/Key:opening_hours#Examples).
| `image`               | A URL of an image for the venue. We try to make this specific to the venue and not generic for the brand that is operating the venue.
| `located_in`          | The name of the feature that this feature is located in.
| `located_in:wikidata` | The [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) [item ID](https://www.wikidata.org/wiki/Help:Items) for the brand or chain of the feature that this feature is located in. This is a machine-readable identifier counterpart for the human-readable `located_in` above.
| `nsi_id`              | The [Name Suggestion Index](https://nsi.guide/) (NSI) ID for the feature. NSI IDs aren't stable, so you may require [old NSI data](https://github.com/osmlab/name-suggestion-index/tree/main/dist) if you are working with old ATP data.

### Extras

Spiders can also include extra fields that will show up but aren't necessarily documented outside their source code.
We aim for them to be consistent with [OpenStreetMap tagging](https://wiki.openstreetmap.org/wiki/Main_Page).
If enough spiders find interesting things to include in an extra property, it might be included here in the documentation in the future.

## Categories

Along with the above properties we aim to output [OpenStreetMap categories](https://wiki.openstreetmap.org/wiki/Map_features) as properties on the GeoJSON Feature.
