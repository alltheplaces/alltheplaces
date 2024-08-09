## Naming your spider

With so many spider files it is important that we maintain
a high level of naming consistency.
At the time of writing there is a
[single directory](../locations/spiders)
containing all of our spiders.

The file and the spider within it should share the same name.
The name should reflect the brand or company name (operator) that
the spider is for. Lower case characters must be used.
If your Python file is `great_name.py` then your spider
should look something like:

```python
import scrapy

class GreatNameSpider(scrapy.Spider):
    name = "great_name"
```

The camel case approach illustrated for the class name
is further recommended. If you know the company / brand
that you are spidering only has locations in one country then it
is helpful to suffix your name with the
[ISO alpha-2 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
for that country. For example,  if `great_name` only had locations
in South Africa, then name the spider file `great_name_za.py`.
Internally, it should look something like:

```python
import scrapy

class GreatNameZASpider(scrapy.Spider):
    name = "great_name_za"
```

If a brand / company is present in multiple territories, and
the spider is able to access all of these using a common approach /
API, then do not qualify the spider name with a country code.
An example of this would be the
[Decathlon spider](../locations/spiders/decathlon.py).

Sometimes things get a little complex. There is a primary
[mcdonalds.py](../locations/spiders/mcdonalds.py) spider which
is able to process many major countries with a common API.
There are country specific spiders, e.g.
[mcdonalds_pt.py](../locations/spiders/mcdonalds_pt.py),
which cover a single territory.
There are also some McDonald's spiders which cover
a small number of countries with the same approach,
e.g. [mcdonalds_baltics.py](../locations/spiders/mcdonalds_baltics.py).

It is quite important that you only add a two character
suffix to the spider name if you are sure that all POIs generated
by the spider are in the same country. The reason for this
is that [ATP pipeline code](../locations/pipelines/country_code_clean_up.py) will add
this country suffix as the country code to scraped POIs if it
has not been set by the spider itself.

## Next steps

When you know the best naming for your spider, use either [scrapy's genspider](https://docs.scrapy.org/en/latest/topics/commands.html#std-command-genspider) command to start with a basic template, or explore other existing spiders as a basis to start.
