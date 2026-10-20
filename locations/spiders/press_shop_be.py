import json
import re
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_NL, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PressShopBESpider(JSONBlobSpider):
    name = "press_shop_be"
    start_urls = ["https://www.press-shop.be/nl/winkels"]
    brands = {
        "Press Shop & More": ({"brand": "Press Shop", "brand_wikidata": "Q126196511"}, Categories.SHOP_NEWSAGENT),
        "Press Shop": ({"brand": "Press Shop", "brand_wikidata": "Q126196511"}, Categories.SHOP_NEWSAGENT),
        "Relay": ({"brand": "Relay", "brand_wikidata": "Q3424298"}, Categories.SHOP_NEWSAGENT),
        "Vape Shop & More": ({"brand": "Vape Shop & More"}, Categories.SHOP_E_CIGARETTE),
        "Sweet Shop & More": ({"brand": "Sweet Shop & More"}, Categories.SHOP_CONFECTIONERY),
    }

    def extract_json(self, response: TextResponse) -> list[dict]:
        blob = ""
        for script in response.xpath('//script[contains(text(), "self.__next_f.push([1,")]/text()').getall():
            segment = script.split("self.__next_f.push([1,", 1)[1].rsplit("])", 1)[0].strip()
            if segment.startswith('"'):
                blob += json.loads(segment)
        return parse_js_object(blob[blob.find('"shops":[') + len('"shops":') :])

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("latlong"))
        feature["street_address"] = feature.pop("address", None)
        feature["postcode"] = feature.pop("postal", None)
        feature["state"] = feature.pop("region", None)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        title = (item.pop("name") or "").strip()
        for prefix, (attributes, category) in self.brands.items():
            if title.startswith(prefix):
                break
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_shop_type")
            return
        item.update(attributes)
        item["branch"] = title.removeprefix(prefix).strip()
        item["website"] = response.urljoin(feature["url"])

        item["opening_hours"] = OpeningHours()
        hours = feature.get("openingHours") or {}
        for day in DAYS_FULL:
            value = str(hours.get(day.lower()) or "").strip()
            if not value:
                continue
            if value.lower() in CLOSED_NL:
                item["opening_hours"].set_closed(day)
            else:
                for open_time, close_time in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", value):
                    item["opening_hours"].add_range(day, open_time, close_time)

        apply_category(category, item)
        yield item
