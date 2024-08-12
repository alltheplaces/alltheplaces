from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


# There is a sitemap, but it's old
class RiverIslandIEGBSpider(CrawlSpider, StructuredDataSpider):
    name = "river_island_ie_gb"
    item_attributes = {"brand": "River Island", "brand_wikidata": "Q2670328"}
    allowed_domains = ["riverisland.com"]
    start_urls = ["https://www.riverisland.com/river-island-stores"]
    rules = [Rule(LinkExtractor(allow="how-can-we-help/find-a-store/"), callback="parse_sd")]

    def post_process_item(self, item, response, ld, **kwargs):
        item["lat"] = float(ld["latitude"])
        item["lon"] = float(ld["longitude"])
        if item["state"] == "Republic of Ireland":
            item["state"] = None
            item["country"] = "IE"
        else:
            item["country"] = "GB"
        if item["city"] == "United Kingdom":
            item["city"] = None
        yield item
