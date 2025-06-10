import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RiteAidUSSpider(CrawlSpider, StructuredDataSpider):
    name = "rite_aid_us"
    item_attributes = {"brand": "Rite Aid", "brand_wikidata": "Q3433273"}
    start_urls = ["https://www.riteaid.com/locations/index.html"]
    rules = [
        Rule(LinkExtractor(allow=r"/\w{2}\.html$")),
        Rule(LinkExtractor(allow=r"/\w{2}/[^/]+\.html$")),
        Rule(LinkExtractor(allow=r"/\w{2}/[^/]+/[^/]+\.html$"), callback="parse_sd"),
    ]
    wanted_types = ["Store"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None

        if m := re.match(r"Rite Aid #(\d+) (.+)", item.pop("name")):
            item["ref"], item["branch"] = m.groups()

        for department in ld_data["department"]:
            if department["@type"] == "Pharmacy":
                break

        apply_category(Categories.SHOP_CHEMIST, item)

        yield item
