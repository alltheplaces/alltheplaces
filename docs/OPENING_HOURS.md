
## Opening hours

In our experience parsing the opening times for a POI location has been one
of the most time-consuming and brittle operations involved in writing
a spider.

The [StructuredDataParser](./STRUCTURED_DATA.md) has improved the general
handling of opening times as in many cases these are parsed by our
library code, being in a "standard" format. If you get them for "free",
what's not to like?

That said, there are many sites with [APIs (mostly JSON)](./API_SPIDER.md)
and also with standard [HTML (essentially text)](./HARD_WORK_SPIDER.md).
In nearly all these cases some bespoke work will be necessary to decode
the opening hours, if they are wanted. This latter question should be
considered. For a site which has only a few locations it is simple
not worth the effort. Just like it may
[not be worth writing](./WHY_SPIDER.md) a spider at all.
It is generally easier to decode opening hours from a JSON API
than it is from bespoke HTML.

In all cases think about the burden of support for the project.
Use common sense when deciding if to proceed and decode opening hours for a site.
Certainly never write special case code to attempt fix-up of individual
store problems.

### Library support

The above said we do provide some library support
([OpeningHours](../locations/hours.py)) for the handling
of opening hour decode and output.
Note that we
[store the decoded opening hours within ATP](../DATA_FORMAT.md)
using the OSM standard format.
Our [StructuredDataParser](./STRUCTURED_DATA.md) internally uses this
library support itself.

Use of the [OpeningHours](../locations/hours.py) support is best illustrated
by looking at an example. [Greggs](http://www.greggs.co.uk) is a UK
coffee shop / bakery fast food  outlet. It has **over 2,000 locations** which for
the UK is very large. The  opening hours are very variable between different stores
and days of the  week. For example, some stores trade on Sunday, others do not.
The site provides a simple JSON API. The
[greggs_gb.py](../locations/spiders/greggs_gb.py)
spider walks their JSON structure and is able to pull
out the opening hours rather simply using the ATP library support.
The cost-benefit analysis in this case is very much in favour of
us making the effort!


### Reference

::: locations.hours
