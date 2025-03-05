import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BannerHealthSpider(StructuredDataSpider):
    name = "banner_health"
    item_attributes = {"operator": "Banner Health", "operator_wikidata": "Q4856918"}
    allowed_domains = ["bannerhealth.com"]
    start_urls = ["https://www.bannerhealth.com/api/sitecore/location/LocationSearch"]
    wanted_types = ["Hospital"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in (json.loads(response.json()))["LocationModelList"]:
            yield scrapy.Request(url="https://www.bannerhealth.com" + location["LocationURL"], callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.CLINIC, item)
        yield item
