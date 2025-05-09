import json
from typing import Any

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BannerHealthSpider(StructuredDataSpider):
    name = "banner_health"
    item_attributes = {"operator": "Banner Health", "operator_wikidata": "Q4856918"}
    allowed_domains = ["bannerhealth.com"]
    start_urls = ["https://www.bannerhealth.com/api/sitecore/location/LocationSearch"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    wanted_types = ["MedicalClinic"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in (json.loads(response.json()))["LocationModelList"]:
            yield Request(response.urljoin(location["LocationURL"]), callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.CLINIC, item)
        yield item
