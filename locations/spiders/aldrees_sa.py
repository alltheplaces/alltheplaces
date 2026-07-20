import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class AldreesSASpider(Spider):
    name = "aldrees_sa"
    item_attributes = {"brand_wikidata": "Q4652322"}
    start_urls = ["https://www.aldrees.com/english/service-locator"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city in response.xpath('//select[@id="selectBox"]/option'):
            city_name = city.xpath("./text()").get("").strip()
            city_id = city.xpath("./@value").get()
            yield JsonRequest(
                url=f"https://www.aldrees.com/english/ajax_unique.php?data=getData&city_id={city_id}",
                callback=self.parse_locations,
                cb_kwargs=dict(city=city_name),
            )

    def parse_locations(self, response: Response, city: str) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item.pop("phone", None)
            address = clean_address(location["baloon_text"])
            if not re.match(r"[-0][,\s]*[-0]*$", address):
                item["street"] = address.replace("STN_ADDRESS", "")
            item["city"] = city
            if not item.get("street") and location.get("latitude") == "0":
                continue
            apply_category(Categories.FUEL_STATION, item)
            yield item
