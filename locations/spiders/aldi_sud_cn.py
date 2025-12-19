import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AldiSudCNSpider(Spider):
    name = "aldi_sud_cn"
    item_attributes = {"brand_wikidata": "Q41171672", "country": "CN"}
    start_urls = ["https://aldi.cn/ourshops/physicalstore/"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 180}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store_data in re.findall(r"data_json:\s*\'(\{.+?})\'\s*,", response.text):
            store = json.loads(store_data)["fields"]
            item = Feature()
            item["ref"] = store["mapLink"]
            item["branch"] = store["storesName"].removesuffix("店").strip()
            item["addr_full"] = store["storesAddress"]

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, store["startTime"], store["endTime"], "%H:%M:%S")

            item["extras"] = {"map": store["mapLink"]}

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
