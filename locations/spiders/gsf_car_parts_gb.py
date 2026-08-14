import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class GsfCarPartsGBSpider(CrawlSpider, StructuredDataSpider):
    name = "gsf_car_parts_gb"
    item_attributes = {"brand": "GSF Car Parts", "brand_wikidata": "Q80963064"}
    start_urls = ["https://www.gsfcarparts.com/branches"]
    rules = [Rule(LinkExtractor(allow=r"/branches/[^/]+$"), callback="parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "DOWNLOAD_DELAY": 2}
    wanted_types = ["Organization"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("GSF Car Parts - ")
        item["city"] = item.pop("state")
        item["facebook"] = None

        if m := re.search(
            r"\\\"longitude\\\":\\\"(-?\d+\.\d+)\\\",\\\"latitude\\\":\\\"(-?\d+\.\d+)\\\"", response.text
        ):
            item["lat"], item["lon"] = m.groups()

        apply_category(Categories.SHOP_CAR_PARTS, item)

        yield item
