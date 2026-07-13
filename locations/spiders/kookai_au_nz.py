import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class KookaiAUNZSpider(Spider):
    name = "kookai_au_nz"
    item_attributes = {"brand": "Kookaï", "brand_wikidata": "Q1783759"}
    start_urls = ["https://www.kookai.com.au/pages/boutique-locator", "https://www.kookai.co.nz/pages/boutique-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = re.findall(
            r"index:\s*(\d+)\s*,.*?"
            r'name:\s*"([^"]+)"\s*,.*?'
            r'address:\s*"([^"]*)"\s*,.*?'
            r'phone:\s*"([^"]*)"\s*,.*?'
            r"position:\s*\[\s*([-\d.]+)\s*,\s*([-\d.]+)",
            response.text,
            re.S,
        )
        for index, name, address, phone, lat, lon in stores:
            item = Feature()
            if ".co.nz" in response.url:
                item["ref"] = index + "NZ"
            else:
                item["ref"] = index + "AU"
            item["branch"] = name.replace("Kookai ", "")
            item["addr_full"] = address.encode().decode("unicode_escape").replace("<p>", "").replace("<\\/p>", ",")
            item["phone"] = phone
            item["lat"] = lat
            item["lon"] = lon
            yield item
