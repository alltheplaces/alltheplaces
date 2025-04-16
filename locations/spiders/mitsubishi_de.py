from copy import deepcopy
from typing import Iterable

import chompjs
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiDESpider(JSONBlobSpider):
    name = "mitsubishi_de"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://www.mitsubishi-motors.de/haendlersuche"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        return chompjs.parse_js_object(response.xpath("//partnersearch-root/@data-partners").get())

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        yield from self.get_details(item, location)

    def get_details(self, item, location) -> Iterable[Request]:
        yield Request(
            url="https://www.mitsubishi-motors.de/api/psearchPartnerDetailedById?partnerId={}".format(
                location.get("id")
            ),
            callback=self.parse_details,
            meta={"item": item},
        )

    def parse_details(self, response: Response) -> Iterable[Feature]:
        for poi in response.json().get("data", []):
            item = deepcopy(response.meta["item"])
            item["street_address"] = poi.get("street")
            item["postcode"] = poi.get("zip")
            item["city"] = poi.get("city")
            item["phone"] = poi.get("phone")
            item["email"] = poi.get("mail")

            item["website"] = poi.get("baseUrl") or poi.get("parentBaseUrl")
            if item.get("website") and not item["website"].startswith("http"):
                item["website"] = "https://" + item["website"]

            type_id = poi.get("partnerTypID")
            if type_id in ["1", "2", "5", "6"]:
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no(Extras.CAR_REPAIR, item, True)
            elif type_id == "4":
                apply_category(Categories.SHOP_CAR, item)
            elif type_id in ["3", "7"]:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            else:
                self.logger.warning(f"Unknown type code: {type_id}, {item['name']}, {item['ref']}")
            self.crawler.stats.inc_value(f"atp/{self.name}/type_code/{type_id}")
            # TODO: opening hours
            yield item
