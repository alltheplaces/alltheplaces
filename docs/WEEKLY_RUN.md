## The weekly run

Having highly targeted spiders for a limited number of companies and brands means
that they can be run regularly. This is important as things in the real world
change regularly. Companies open new and close old locations. Opening hours can
change. Also, a company can change their website in a way that causes the spider
to no longer function.

### alltheplaces.xyz

For all these reasons we try (at the time of writing) to perform a weekly run of
all the spiders. The output is published on our
website: [alltheplaces.xyz](https://www.alltheplaces.xyz/).
This data set is available as a compressed tar file. Each entry in the tar file
is the [GeoJSON](https://geojson.org/) output from a spider. Some of the fields, which
may be in the GeoJSON, are described in our [data format document](../DATA_FORMAT.md).
For those with knowledge of OpenStreetMap POI tags these will be somewhat familiar.

Given that we publish the data, there should be no reason for you to run all the
spiders yourself. If we all started doing this then a site is far more likely to
engage blocking measures.

### Statistics

Alongside the POI data we further publish reports that help us maintain the
health of the code base. For a list of available reports then see the links on
[alltheplaces.xyz](https://www.alltheplaces.xyz/). Some examples of the
report data includes:

* how many POIs were retrieved by each spider this week and for previous weeks
* how many POIs were retrieved by a spider compared with the total branded count in OSM
