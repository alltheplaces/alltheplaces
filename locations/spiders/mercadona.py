from datetime import datetime
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MercadonaSpider(Spider):
    name = "mercadona"
    item_attributes = {"brand": "Mercadona", "brand_wikidata": "Q377705"}
    start_urls = ["https://storage.googleapis.com/pro-bucket-wcorp-files/json/data.js"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for stores in chompjs.parse_js_object(response.text)["tiendasFull"]:
            item = Feature()
            item["lat"] = stores["lt"]
            item["lon"] = stores["lg"]
            item["ref"] = stores["id"]
            item["postcode"] = stores["cp"]
            item["phone"] = stores["tf"]
            item["street_address"] = stores["dr"]
            item["country"] = stores["p"]
            item["city"] = stores["lc"]
            item["website"] = "https://info.mercadona.es/es/supermercados?s={}&k={}".format(
                item["postcode"], item["ref"]
            )
            item["extras"]["start_date"] = datetime.strptime(stores["fap"], "%d/%m/%Y").strftime("%Y-%m-%d")

            item["opening_hours"] = self.parse_opening_hours(stores["in"], stores["fi"])

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item

    def parse_opening_hours(self, start_times: str, end_times: str) -> OpeningHours:
        oh = OpeningHours()

        for day, start_time, end_time in zip(DAYS[3:] + DAYS[:5], start_times.split("#"), end_times.split("#")):
            if start_time == end_time in ("C", "CR"):
                oh.set_closed(day)
            else:
                oh.add_range(day, start_time, end_time, time_format="%H%M")

        return oh
