from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiUASpider(JSONBlobSpider):
    name = "mitsubishi_ua"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://mitsubishi-motors.com.ua/find-a-dealer"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.__NUXT__")]/text()').re_first(
                r"dealers\s*=\s*\'(\[.+?\])\'"
            ),
            unicode_escape=True,
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["latlng"].split(",")
        item["street_address"] = item.pop("addr_full", None)
        item["website"] = feature.get("website_link")
        item["extras"]["brand:website"] = response.urljoin(f'?dealer={item["ref"]}')

        departments = {
            department["title"]: {"phones": department["phones"], "schedule": department["schedule"]}
            for department in feature["departments"]
        }
        SALES = "Відділ продажу"
        SERVICE = "Відділ сервісу"
        category = ""

        if SALES in departments:
            category = SALES
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, SERVICE in departments)
        elif SERVICE in departments:
            category = SERVICE
            apply_category(Categories.SHOP_CAR_REPAIR, item)

        phones = departments[category].get("phones") or ""
        item["phone"] = phones.replace(",", "; ")

        yield item
