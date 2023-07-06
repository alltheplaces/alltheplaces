# All The Places Data Format

The output of the periodic run of all spiders posted on https://www.alltheplaces.xyz/ is a .tar.gz collection of each spider's output. Each spider produces a single GeoJSON `FeatureCollection` where each `Feature` contains the data for a single scraped item. Along with the GeoJSON output, the collection includes logs and statistics, which can help understand what happened during the spider's run.

## Identifier

Each GeoJSON feature will have an `id` field. The ID is a hash based on the `ref` and `@spider` fields and should be consistent between builds.

Data consumers might use the `id` field to determine if new objects show up or disappear between builds. Occasionally, the authors of spiders will change the spider name or the website we spider will change the identifiers used for the store. In these cases, the ID field in our output will change dramatically. At this time, we don't make an attempt to link the old and new IDs. Also, in some cases a spider author is unable to find a stable identifier for an item and each run will get a unique identifier.

## Geometry

In most cases, the feature will include a `geometry` field following [the GeoJSON spec](https://tools.ietf.org/html/rfc7946#section-3.1). There are some spiders that aren't able to recover a position from the venue's website. In those cases, the geometry is set to `null` and only the properties are included.

Although it's not supported at the time of this writing, we hope to include a geocoding step in the pipeline so that these feature will get a position added.

## Properties

Each GeoJSON feature will have a `properties` object with the following keys:

| Name                  | Required? | Description |
|-----------------------|---|---|
| `ref`                 | Yes | A unique identifier for this feature inside this spider. The code that generates the output will remove duplicates based on the value of this key.
| `@spider`             | Yes | The name of the spider that produced this feature. It is [specified in each spider](https://github.com/alltheplaces/alltheplaces/blob/11d9be56515ef0f6419e001b1950f69d28d4f400/locations/spiders/apple.py#L9), so it doesn't necessarily related to the file name of the spider.
| `name`                | No  | The name of the feature. This is usually extracted from the venue's page, so it will probably be different per feature. This is often the location specific part of a chain location's name, like the name of the mall it's in, without the chain name included.
| **Brand**             |     | _Information about the brand that operates or owns the venue_
| `brand`               | No  | The brand or chain name of the feature. This will generally be the same for most features outputted by a scraper. Some scrapers will output for companies that own multiple brands, like Duane Reade and Walgreens for the Walgreens scraper.
| `brand:wikidata`      | No  | The [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) [item ID](https://www.wikidata.org/wiki/Help:Items) for the brand of the feature. This is a machine-readible identifier counterpart for the human-readible `brand` above.
| **Address**           |     | _Information about the address of the venue_
| `addr:full`           | No  | The full address for the venue in one line of text. Usually this follows the format of street, city, province, postcode address. This field might exist instead of the other address-related fields, especially if the spider can't reliably extract the individual parts of the address.
| `addr:housenumber`    | No  | The house number part of the address.
| `addr:street`         | No  | The street name.
| `addr:street_address` | No  | The street address, including street name and house number and/or name.
| `addr:city`           | No  | The city part of the address.
| `addr:state`          | No  | The state or province part of the address.
| `addr:postcode`       | No  | The postcode part of the address.
| `addr:country`        | No  | The country part of the address.
| **Contact**           |     | _Contact information for the venue_
| `phone`               | No  | The telephone number for the venue. Note that this is usually pulled from a website assuming local visitors, so it probably doesn't include the country code.
| `website`             | No  | The website for the venue. We try to make this a URL specific to the venue and not a generic URL for the brand that is operating the venue.
| `contact:email`       | No  | The email address for the venue. We try to make this an email specific to the venue and not a generic email for the brand that is operating the venue.
| `contact:twitter`     | No  | The twitter account for the venue. We try to make this specific to the venue and not generic for the brand that is operating the venue.
| `contact:facebook`    | No  | The facebook account for the venue. We try to make this specific to the venue and not generic for the brand that is operating the venue.
| **Other**             |     | _Other information about the venue_
| `opening_hours`       | No  | The opening hours for the venue. When we can, the format for this field follows [OpenStreetMap's `opening_hours` format](https://wiki.openstreetmap.org/wiki/Key:opening_hours#Examples).
| `image`               | No  | A URL of an image for the venue. We try to make this specific to the venue and not generic for the brand that is operating the venue.
| `located_in`          | No  | The name of the feature that this feature is located in.
| `located_in:wikidata` | No  | The [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) [item ID](https://www.wikidata.org/wiki/Help:Items) for the brand or chain of the feature that this feature is located in. This is a machine-readible identifier counterpart for the human-readible `located_in` above.
| `nsi_id`              | No  | The [Name Suggestion Index](https://nsi.guide/) (NSI) ID for the feature. NSI IDs aren't stable, so you may require [old NSI data](https://github.com/osmlab/name-suggestion-index/tree/main/dist) if you are working with old ATP data.                                                                         |

Spiders can also include extra fields that will show up but aren't necessarily documented outside their spider source code. If enough spiders find interesting things to include in an extra property, it might be included here in the documentation in the future.
