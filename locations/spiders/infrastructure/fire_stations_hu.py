import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FireStationsHUSpider(Spider):
    name = "fire_stations_hu"
    start_urls = ["https://www.katasztrofavedelem.hu/33856/tuzoltosagok-elhelyezkedese"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//script[contains(text(), "office_Map_data")]/text()').re_first(
                r"office_Map_data = (\[{.+}]);"
            )
        ):
            item = DictParser.parse(location)
            if item["email"]:
                item["email"] = item["email"].split(" ", 1)[0]  # .replace(" ", ";")
            # TODO: image_id

            if location["category"] == "5":
                item["extras"]["fire_station:type"] = "voluntary"
            elif location["category"] == "4":
                continue
            elif location["category"] == "3":
                item["extras"]["fire_station:type"] = "municipal"
                item["name"] = item["name"].replace("ÖTP", "Önkormányzati Tűzoltó-parancsnokság")
            elif location["category"] == "2":
                item["extras"]["fire_station:type"] = "local_station"
                item["name"] = item["name"].replace("KŐ", "Katasztrófavédelmi Őrs")
            elif location["category"] == "1":
                item["extras"]["fire_station:type"] = "main_station"
                item["name"] = item["name"].replace("HTP", "Hivatásos Tűzoltó-parancsnokság")

            apply_category(Categories.FIRE_STATION, item)

            yield item
