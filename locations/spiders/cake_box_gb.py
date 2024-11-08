import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature


class CakeBoxGBSpider(Spider):
    name = "cake_box_gb"
    item_attributes = {"brand": "Cake Box", "brand_wikidata": "Q110057905"}
    start_urls = ["https://www.cakebox.com/storelocator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.xpath('//script[contains(text(), "jsonLocations")]/text()').get()
        data = re.sub(r"^.*jsonLocations: ", "", data, flags=re.DOTALL)
        data = re.sub(r",\s+imageLocations.*$", "", data, flags=re.DOTALL)
        jsondata = json.loads(data)
        for location in jsondata["items"]:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            sel = location["popup_html"]
            item["city"] = re.search(r"(?<=City: )[^<]+", sel).group(0)
            item["street_address"] = re.search(r"(?<=Address: )[^<]+", sel).group(0)
            item["postcode"] = re.search(r"(?<=Zip: )[^<]+", sel).group(0)
            apply_category({"shop": "bakery"}, item)
            yield item
