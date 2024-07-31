
## The store locator has an API

It can be very easy writing a spider for a site with
a good [sitemap](./SITEMAP.md) and also good [structured data](./STRUCTURED_DATA.md)
pages. Not all sites work this way and with these you will have more work to do.
There are a good number of sites that employ their
own bespoke API (typically returning [JSON data](https://en.wikipedia.org/wiki/JSON)).
These APIs exhibit a good degree of similarity in terms of the fields returned.

The first thing to do is to figure out that **there is an API** and **how it is driven**.
With a [web development console](https://docs.scrapy.org/en/latest/topics/developer-tools.html)
enabled, navigate using the store locator, to one of the store pages. Then with a per POI
field like phone number or postcode search for that string in the network transfers section
of the console. If the data has come in via an API call you will quickly see this and also by
examining the URL and headers for the data transfer start to understand the API.

If you find that the POI data you want is present in the web page itself as HTML then
most likely you will be having to write a spider the hard way.

The rest of this page discusses some different kinds of JSON API by example.

### DictParser, a helper for POI JSON

In nearly all cases you should find that our [DictParser](../locations/dict_parser.py)
class can help keep your code tight. There are only so many ways that you
can name a field `latitude`. The `DictParser` code tries those different ways for
this and other fields. Of course, it will not get everything right for every API.
This is where you may have to write a little code yourself, but a lot
less than otherwise.

### The simple life, one API call, all sites returned

Sometimes a single HTTP request can return a JSON structure giving the details for
all stores in the group. You've got lucky. Use `DictParser` to do the best it can
before fixing any mistakes or additions after it returns. Some examples:

* [greggs_gb.py](../locations/spiders/greggs_gb.py)
* [mcdonalds_it.py](../locations/spiders/mcdonalds_it.py) (adjusts JSON before calling DictParser)

### Driving an API by position, city or postcode

Sometimes an API requires an area query and one call may not suffice.
You are going to have to figure out the best approach. To start with you must
know what you are dealing with:

* can I query by postcode?, by city?
* can I query by position (latitude/longitude)?
* can I increase the number of POIs returned by a single call?
* can I increase the radial extent of the query?

We provide a certain amount of library support for driving such APIs with data.
The [`geonames`](https://www.geonames.org/) countries and cities dataset is
a dependency of the project. There are [postcode datasets](../locations/searchable_points/postcodes)
for various territories. There are position point files to cover
[various territories at various densities](../locations/searchable_points).
The data should be accessed through the interfaces we have provided
on [geo.py](../locations/geo.py).

All the above is best illustrated with some further examples:

* [spar_gb.py](../locations/spiders/spar_gb.py) (drive query API by postcode)
* [petsathome_gb.py](../locations/spiders/pets_at_home_gb.py) (query GB at 20km point resolution)
* [thebodyshop.py](../locations/spiders/the_body_shop.py) (use sitemap to generate API parameters)
