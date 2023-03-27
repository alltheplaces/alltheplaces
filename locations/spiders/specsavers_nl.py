from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SpecsaversNLSpider(CrawlSpider, StructuredDataSpider):
    name = "specsavers_nl"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    start_urls = ["https://www.specsavers.nl/winkelzoeker/winkeloverzicht"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.specsavers\.nl\/winkelzoeker\/(?!winkeloverzicht)((?!<\/)(.(?!-hoorzorg))+)$"
            ),
            callback="parse_sd",
        )
    ]
    wanted_types = ["Optician"]

    def post_process_item(self, item, response, ld_data):
        item.pop("email")
        item.pop("facebook")
        yield item
