import html

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BishopsArmsSESpider(CrawlSpider, StructuredDataSpider):
    name = "bishops_arms_se"
    item_attributes = {"brand": "Bishops Arms", "brand_wikidata": "Q10430084"}
    start_urls = ["https://www.bishopsarms.com/vara-hotell/", "https://www.bishopsarms.com/vara-pubar/"]
    rules = [
        Rule(LinkExtractor(allow="/vara-hotell/", restrict_xpaths="//main//a"), "parse"),
        Rule(LinkExtractor(allow="/vara-pubar/", restrict_xpaths="//main//a"), "parse"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = html.unescape(item["name"])
        if item.get("street_address"):
            item["street_address"] = html.unescape(item["street_address"])
        if item.get("city"):
            item["city"] = html.unescape(item["city"])

        if item["name"].startswith("Hotel "):
            apply_category(Categories.HOTEL, item)
            item["branch"] = item.pop("name").removeprefix("Hotel Bishops Arms ")
        else:
            apply_category(Categories.PUB, item)
            item["branch"] = item.pop("name").removeprefix("The Bishops Arms ")

        yield item
