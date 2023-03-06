from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SpecsaversNOSpider(CrawlSpider, StructuredDataSpider):
    name = "specsavers_no"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    start_urls = ["https://www.specsavers.no/finn-din-butikk/komplett-butikkoversikt"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.specsavers\.no\/finn-din-butikk\/(.+)$"), callback="parse_sd"
        )
    ]
    wanted_types = ["Optician"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        item.pop("facebook")
        yield item
