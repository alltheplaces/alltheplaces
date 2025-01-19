# All The Places Data Format

The output of the periodic run of all spiders posted on https://www.alltheplaces.xyz/ is a .zip of each spider's output. Each spider produces a single GeoJSON `FeatureCollection` where each `Feature` contains the data for a single scraped item. Along with the GeoJSON output, the collection includes logs and statistics, which can help understand what happened during the spider's run.

## Identifier

Each GeoJSON feature will have an `id` field. The ID is a hash based on the `ref` and `@spider` fields and *should be* consistent between builds.

Data consumers might use the `id` field to determine if new objects show up or disappear between builds. Occasionally, the authors of spiders will change the spider name or the website we spider will change the identifiers used for the store. In these cases, the ID field in our output will change dramatically. At this time, we don't make an attempt to link the old and new IDs. Also, in some cases a spider author is unable to find a stable identifier for an item and each run will get a unique identifier.

## Geometry

In most cases, the feature will include a `geometry` field following [the GeoJSON spec](https://tools.ietf.org/html/rfc7946#section-3.1). There are some spiders that aren't able to recover a position from the feature's website. In those cases, the geometry is set to `null` and only the properties are included.

Although it's not supported at the time of this writing, we hope to include a geocoding step in the pipeline so that these feature will get a position added.

## Properties

Each GeoJSON feature will have a `properties` object with as many of the following properties as possible, however only `@spider` is guaranteed:

| Name                  | Description |
|-----------------------|---|
| `ref`                 | A unique identifier for this feature inside this spider. The code that generates the output will remove duplicates based on the value of this key. It forms part of the feature [`id`](#identifier).
| `@spider`             | The name of the spider that produced this feature. It is [specified in each spider](https://github.com/alltheplaces/alltheplaces/blob/11d9be56515ef0f6419e001b1950f69d28d4f400/locations/spiders/apple.py#L9), so it isn't necessarily related to the file name/class name of the spider, for example [99_bikes_au](https://github.com/alltheplaces/alltheplaces/blob/master/locations/spiders/99_bikes_au.py)
| `@source_uri`         | A URI describing where this feature was obtained. This is not guaranteed to be viewable in a web browser.
| `branch`              | This is often the location specific part of a chain location's name, like the name of the mall or city it is in, without the brand name included.
| `name`                | The name of the feature. Ideally the fascia, however this is often a combination of the brand and the branch.
| **Brand**             | _Information about the brand for the feature._
| `brand`               | The brand or chain name of the feature. This will generally be the same for most features outputted by a scraper. Some scrapers will output for companies that own multiple brands, like Duane Reade and Walgreens for the Walgreens scraper.
| `brand:wikidata`      | The [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) [item ID](https://www.wikidata.org/wiki/Help:Items) for the brand of the feature. This is a machine-readable identifier counterpart for the human-readable `brand` above.
| **Operator**          | _Information about the operator of the feature._
| `operator`            | The name of the operator of the feature. See the [OpenStreetMap Wiki](https://wiki.openstreetmap.org/wiki/Key:operator) for more details about the difference between `brand` and `operator`.
| `operator:wikidata`   | The [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) [item ID](https://www.wikidata.org/wiki/Help:Items) for the operator of the feature. This is a machine-readable identifier counterpart for the human-readable `operator` above.
| **Address**           | _Information about the address of the feature._ See further discussion [below](#addresses) for detailed description.
| `addr:full`           | The full address of a feature in one line of Unicode text as provided by source data. Usually this follows the format of `addr:street_address addr:city addr:state addr:postcode` but the format is source and country-specific.
| `addr:housenumber`    | The house number part of the address. Despite "number" in this property name, values are not limited to numerals and may contain any Unicode characters (an example being "2A").
| `addr:street`         | The street name part of the address, including any street type applicable (such as "Road" or "Street").
| `addr:street_address` | The street address including properties such as `addr:unit`, `addr:floor`, `addr:housenumber`, `addr:street`.
| `addr:city`           | The lowest level administrative subdivision (city, town, suburb or similar) which source data provides for an address.
| `addr:state`          | The first level administrative subdivision (state, province or similar) of an address. Typically the subdivision level which [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) attemps to model but where [territorial disputes](https://en.wikipedia.org/wiki/List_of_territorial_disputes) apply, the convention used by source data will be adhered to (typically de-facto recognition of territory) in preference to whatever territory is modelled by ISO 3166-2. Users of All the Places data may wish to ignore `addr:state` and instead determine tertitorial control using [point-in-polygon (PIP)](https://en.wikipedia.org/wiki/Point_in_polygon) techniques with user choice of territory polygons.
| `addr:postcode`       | The postcode part of the address.
| `addr:country`        | The country part of the address as an [ISO 3166-1 alpha-2 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). Similar to [OpenStreetMap's `addr:country`](https://wiki.openstreetmap.org/wiki/Key:addr:country), this field may contain ambiguous and/or unstable user-assigned ISO 3166-1 alpha-2 codes such as ["XK" for Kosovo](https://en.wikipedia.org/wiki/XK_(user_assigned_code)). [Territorial disputes](https://en.wikipedia.org/wiki/List_of_territorial_disputes) are another important consideration. All the Places attempts to follow the convention of source data and will populate `addr:country` as best as possible to match source data (typically de-facto territory recognition). If source data does not specify a country/territory, All the Places will then attempt to estimate a de-facto territory with reverse geocoding techniques. Users of All the Places data may wish to ignore `addr:country` and instead determine tertitorial control using [point-in-polygon (PIP)](https://en.wikipedia.org/wiki/Point_in_polygon) techniques with user choice of territory polygons.
| **Contact**           | _Contact information for the feature._
| `phone`               | The telephone number(s) for the feature typically in [ITU-T E.164 format](https://en.wikipedia.org/wiki/E.164), separated by `;` if there is more than one number. Phone numbers are reformatted using the [phonenumbers library](https://pypi.org/project/phonenumbers/) however invalid numbers will still be returned as-is if they cannot be parsed. Thus values are not always guaranteed to be in ITU-T E.164 format and may be missing country dialling codes. Due to the complexities of [territorial disputes](https://en.wikipedia.org/wiki/List_of_territorial_disputes) and ambiguity in source data, the process for reformatting phone numbers may in rare circumstances result in invalid country dialling codes or phone number formatting being applied.
| `website`             | The website for the feature. We try to make this a URL specific to the feature and not a generic URL for the brand that is operating the feature.
| `email`               | The e-mail address(es) for the feature in [RFC 5322 Addr-Spec format](https://datatracker.ietf.org/doc/html/rfc5322#section-3.4.1), separated by `;` if there is more than one e-mail address. We try to make this an email specific to the feature and not a generic email for the brand that is operating the feature.
| `contact:twitter`     | The X (formerly Twitter) account name for the feature. We try to make this specific to the feature and not generic for the brand that is operating the feature.
| `contact:facebook`    | The Facebook account name for the feature. We try to make this specific to the feature and not generic for the brand that is operating the feature.
| **Other**             | _Other information about the feature._
| `opening_hours`       | The opening hours for the feature in a simplifed variant of [OpenStreetMap's `opening_hours` format](https://wiki.openstreetmap.org/wiki/Key:opening_hours#Examples). See further discussion [below](#opening-hours) for detailed description.
| `image`               | A URL of an image for the feature. We try to make this specific to the feature and not generic for the brand that is operating the feature.
| `located_in`          | The name of the feature that this feature is located in.
| `located_in:wikidata` | The [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) [item ID](https://www.wikidata.org/wiki/Help:Items) for the brand or chain of the feature that this feature is located in. This is a machine-readable identifier counterpart for the human-readable `located_in` above.
| `nsi_id`              | The [Name Suggestion Index](https://nsi.guide/) (NSI) ID for the feature. NSI IDs aren't stable, so you may require [old NSI data](https://github.com/osmlab/name-suggestion-index/tree/main/dist) if you are working with old ATP data.
| `end_date`            | `end_date=yes` is applied when given location is closed at unknown date and can be assumed to not operate right now, `end_date` may also have values in year-month-day format, including future dates for planned closures. If the POI has been deleted entirely in the source data, ATP will stop returning the former POI.

All translatable property values are supplied in the primary local language and are UTF-8 strings. For example, `name` or `branch` for a feature in Japan will typically be Japanese UTF-8 encoded text (ISO 639-1 alpha-2 code of "ja"). Address fields are also typically supplied in the primary local langauge. If other translations are available for a property value, the translated property values are supplied as [extra fields](#extras). Continuing the example of a feature in Japan, if an English translation for `name` or `branch` is additionally available, it will be present as `name:en` or `branch:en` as an [extra field](#extras). Language code suffixes are lower case ISO 639-1 alpha-2 codes.

### Addresses

All the Places uses a simplified model of [OpenStreetMap's `addr:*` properties](https://wiki.openstreetmap.org/wiki/Key:addr:*). Around the world, address information is written in a wide variety of ways. All the Places does not attempt to model every type of written address and instead typically expects users of All the Places data to self-interpret address information provided by sources (typically as a single Unicode string).

For example, in some countries, a house may be located within a 5th level subdivision of that country, whilst a house in a different country may be located within a 3rd level subdivision. All the Places will generally provide `addr:full` with address information exactly as written in source data. If source data allows, All the Places may also output `addr:state` as the first level administrative subdivision (similar to what [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) models) and `addr:city` as the lowest level subdivision or a subdivision level which prevents ambiguity of `addr:street`.

Some All the Places spiders may model more precise and/or country-specific address information as [extra properties](#extras) if the source data provides a precise model of address information. Examples of such properties are `addr:unit`, `addr:floor`, `addr:hamlet` and `addr:suburb`.

In the case of features residing in locations subject to [territorial disputes](https://en.wikipedia.org/wiki/List_of_territorial_disputes), All the Places will attempt to follow the typically de-facto recongition of territory made by source data. Where source data fails to unambiguously state a de-facto territory, All the Places will apply reverse geocoding techniques to estimate a de-facto territory in preference to estimating a de-jure territory per standard such as [ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1) or [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). Users of All the Places data may wish to ignore `addr:country` and `addr:state` and instead determine tertitorial control using [point-in-polygon (PIP)](https://en.wikipedia.org/wiki/Point_in_polygon) techniques with user choice of territory polygons.

### Extras

Spiders can also include extra properties that will be provided in output formats such as GeoJSON. We aim for such extra properties to be consistent with [OpenStreetMap tagging](https://wiki.openstreetmap.org/wiki/Main_Page). Otherwise, source code of the spider in question is expected to contain documentation describing the extra properties.

Common extra properties include:
* Translated values for properties including `name`, `branch` and properties within the `addr` namespace.
* Additional names, abbreviations and reference numbers/codes for a feature.
* Presence of amenities within features including restrooms, car parking and seating where such amenities are not typically mapped as separate OpenStreetMap nodes. Refer to the [Extras enum](https://github.com/alltheplaces/alltheplaces/blob/master/locations/categories.py) within All the Places source code for some documentation of amenity tags which are typically added by spiders.
* Additional social media handles within the `contact:` namespace.

If enough spiders find interesting things to include in an extra property, it might be included here in the documentation in the future.

## Opening Hours

The format of the `opening_hours` property is a simplifed variant of [OpenStreetMap's `opening_hours` format](https://wiki.openstreetmap.org/wiki/Key:opening_hours#Examples). A few important limitations are:

* Days are typically omitted from the opening hours string when the entry is closed on that day. OpenStreetMap typically uses this approach too. All the Places is transitioning towards explicitly noting closures (example of `Mo-Tu closed`) where source data is reasonably unambiguous.
* In some cases only some days of week can be parsed due to ambiguity or missing information in source data. The unparsable days are omitted from the opening hours string even though the feature is not closed. In many cases it is impossible to distinguish from source data whether the feature is open or closed on the particular day of the week. Refer to [this issue](https://github.com/alltheplaces/alltheplaces/issues/6943) for more information.
* Opening hours information provided in source data may only apply to the current and/or next week and not represent typical opening hours expected for most weeks of a year. All the Places therefore may only be able to output opening hours strings which are temporary in nature for the current week only, inclusive of temporary changes due to public holidays. Consumers of All the Places data are recommended to check multiple data outputs from previous All the Places crawls to find the most common (regular) opening hours of a feature.
* Opening hours format does not match OSM syntax exactly, particularly in the case of [time ranges extending across midnight](https://github.com/alltheplaces/alltheplaces/discussions/4959).
* `Mo-Su closed` typically indicates POI closed temporarily for reasons of maintenance and refurbishment. POIs that are permanently closed but listed by source data are returned with the `end_date` field (see `end_date` specification for details).

## Categories

Along with the above properties we aim to output [OpenStreetMap categories](https://wiki.openstreetmap.org/wiki/Map_features) as properties on the GeoJSON Feature. For multi-purpose features, such as a shop which is primarily known as a bakery but also sells beverages, we aim to follow [OpenStreetMap's convention of choosing only the dominant category](https://wiki.openstreetmap.org/wiki/Key:shop#Multi-purpose_shops). Continuing the example, the feature output by All the Places will have a category of `shop=bakery` rather than a category list of `shop=bakery;beverages`.

For some types of features such as fuel stations, All the Places will output multiple features and apply separate categories to each. For example, a fuel station and adjoining convenience store where payment is made for fuel are typically considered separate features by All the Places because the fuel station and convenience store typically have different branding applied. However, a restroom within the convenience store will typically not be output as a separate feature and will instead have a `toilets=yes` [extra property](#extras) applied to the convenience store feature.

Note that All the Places will attempt to obtain category information from [NSI data](https://github.com/osmlab/name-suggestion-index/tree/main/dist) if a spider fails to explicitly set a category for a feature.

[Extra properties](#extras) of a brand or operator in NSI will also typically be copied to a feature output by All the Places unless a spider explicitly disables such copying of [extra properties](#extras) from a brand or operator in NSI.

## Data quality

Note that the All the Places project collects data from original sources. Most mistakes or inaccuracies present in the original sources will be reproduced by the datasets published by All the Places.

In addition, parts of the data may be missing or not parsed, especially in cases where the original source is hard to parse or crawling failed for some reason. Data may also be outdated - either due to being outdated in original source, an update happening since data was last crawled, or due to a failing spider.

Data quality is not consistent and will vary significantly between spiders. Note that global, less specific spiders are especially likely to have inaccurate data.
