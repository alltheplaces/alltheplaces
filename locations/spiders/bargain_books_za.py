import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BargainBooksZASpider(Spider):
    name = "bargain_books_za"
    item_attributes = {"brand": "Bargain Books", "brand_wikidata": "Q116741024"}
    start_urls = ["https://www.bargainbooks.co.za/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for match in re.finditer(r'\$R\[\d+\]=(\{id:"[0-9a-f-]{8}-)', response.text):
            store_str = self.extract_balanced_object(response.text, match.start(1))
            if not store_str:
                continue
            store = chompjs.parse_js_object(re.sub(r"\$R\[\d+\]=", "", store_str))

            if "head office" in store["name"].lower():
                continue

            item = Feature()
            item["ref"] = store["id"]
            item["lat"] = store["lat"]
            item["lon"] = store["lng"]
            item["branch"] = store["name"]
            item["addr_full"] = store["address"]
            item["city"] = store["city"]
            item["state"] = store["province"]
            item["phone"] = store["phone"]

            item["opening_hours"] = OpeningHours()
            for days, hours_key in [
                (["Mo", "Tu", "We", "Th", "Fr"], "hours_weekday"),
                (["Sa"], "hours_saturday"),
                (["Su"], "hours_sunday"),
            ]:
                hours = store.get(hours_key)
                if not hours:
                    continue
                if hours.lower() == "closed":
                    item["opening_hours"].set_closed(days)
                    continue
                open_time, close_time = hours.split("-")
                if close_time <= open_time:
                    continue
                for day in days:
                    item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

            apply_category(Categories.SHOP_BOOKS, item)

            yield item

    @staticmethod
    def extract_balanced_object(text: str, start: int) -> str | None:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            char = text[i]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
        return None
