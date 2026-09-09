import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MillersAleHouseSpider(scrapy.Spider):
    name = "millers_ale_house"
    item_attributes = {"brand": "Miller's Ale House", "brand_wikidata": "Q6858987"}
    start_urls = ["https://millersalehouse.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Every page on the site embeds a JS array of all locations (used to
        # power the "nearby locations" widget), so a single page load is
        # enough to discover the full store list with address/phone/coords.
        blob = response.xpath('//script[contains(text(), "var locations = ")]/text()').re_first(
            r"var locations = (\[.*?\]);"
        )
        for store in json.loads(blob):
            store["lat"] = store["latlng"]["lat"]
            store["lon"] = store["latlng"]["lng"]
            yield scrapy.Request(store["url"], callback=self.parse_store, cb_kwargs={"store": store})

    def parse_store(self, response: Response, store: dict) -> Any:
        item = DictParser.parse(store)
        item["branch"] = item.pop("name")
        item["website"] = store["url"]

        schema = json.loads(response.xpath('//script[@class="saswp-schema-markup-output"]/text()').get())[0]

        # openingHours mixes "Dine-In" and "Takeout & Delivery" hours in one
        # HTML-tagged string; only the dine-in section reflects when the
        # restaurant itself is open. A handful of locations have this field
        # as an empty list instead of a populated string.
        opening_hours_raw = schema.get("openingHours")
        if opening_hours_raw and isinstance(opening_hours_raw, str):
            dine_in_hours = re.sub(r"<[^>]+>", "", opening_hours_raw.split("Takeout")[0])
            oh = OpeningHours()
            oh.add_ranges_from_string(dine_in_hours)
            item["opening_hours"] = oh

        apply_category(Categories.RESTAURANT, item)

        yield item
