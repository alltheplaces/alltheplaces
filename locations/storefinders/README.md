
## Store finders

Many store locator pages are powered by back-end APIs served by a
contracted third party _"brander marketing / store finder"_ company
e.g. [RioSEO](https://www.rioseo.com/local-marketing-solutions/store-locator-software/).
There is no need to duplicate the code to talk these store finder companies across
multiple spiders. Rather a [common spider is written in this directory](./rio_seo.py)
which can then be called on by brand specific code e.g.

* [United Band](../spiders/united_bank_us.py#L5)
* [Pandora](../spiders/pandora.py#L7)

In most cases the brand specific code will link the brand to a
[name suggestion index](../../docs/WIKIDATA.md#name-suggestion-index-nsi)
entry and apply any tweaks that the author considers appropriate as illustrated above.
