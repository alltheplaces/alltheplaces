from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser


# There are a few stores in Ireland.
class RiverIslandGBSpider(CrawlSpider):
    name = "riverisland_gb"
    item_attributes = {
        "brand": "RIVER ISLAND",
        "brand_wikidata": "Q2670328",
    }
    allowed_domains = ["riverisland.com"]
    start_urls = ["https://www.riverisland.com/river-island-stores"]
    rules = [
        Rule(
            LinkExtractor(allow="how-can-we-help/find-a-store"),
            callback="parse_func",
            follow=False,
        )
    ]

    def parse_func(self, response):
        ld = LinkedDataParser.find_linked_data(response, "ClothingStore")
        if ld:
            item = LinkedDataParser.parse_ld(ld)
            item["lat"] = float(ld["latitude"])
            item["lon"] = float(ld["longitude"])
            item["ref"] = response.url
            if item["state"] == "Republic of Ireland":
                item["state"] = None
                item["country"] = "IE"
            else:
                item["country"] = "GB"
            if item["city"] == "United Kingdom":
                item["city"] = None
            yield item
