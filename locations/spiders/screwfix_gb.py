from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ScrewfixGBSpider(CrawlSpider, StructuredDataSpider):
    name = "screwfix_gb"
    item_attributes = {"brand": "Screwfix", "brand_wikidata": "Q7439115"}
    allowed_domains = ["www.screwfix.com"]
    start_urls = ["https://www.screwfix.com/stores/all"]
    rules = [Rule(LinkExtractor(allow=r"\/stores\/([A-Z][A-Z][0-9])\/.+$"), callback="parse")]
    wanted_types = ["HardwareStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["phone"] = None

        if item["name"].startswith("Screwfix City "):
            item["branch"] = item.pop("name").removeprefix("Screwfix City ")
            item["name"] = "Screwfix City"
        else:
            item["branch"] = item.pop("name").removeprefix("Screwfix ")
            item["name"] = "Screwfix"

        apply_category(Categories.SHOP_DOITYOURSELF, item)

        yield item
