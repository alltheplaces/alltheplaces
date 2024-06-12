import html
import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class TexacoCentralAmericaSpider(Spider):
    name = "texaco_central_america"
    item_attributes = {"brand": "Texaco", "brand_wikidata": "Q775060"}
    start_urls = [
        "https://www.texacocontechron.com/estaciones-de-servicio/",
        "https://www.texacocontechron.com/gt/estaciones-de-servicio/",
        "https://www.texacocontechron.com/hn/estaciones-de-servicio/",
        "https://www.texacocontechron.com/pa/estaciones-de-servicio/",
        "https://www.texacocontechron.com/sv/estaciones-de-servicio/",
    ]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state in json.loads(re.search(r"var dataSedes = ({.+});", response.text).group(1)).values():
            for location in state:
                item = Feature()
                item["name"] = html.unescape(location["nombre"])
                item["addr_full"] = html.unescape(location["ubicacion"]["address"])
                item["lat"] = location["ubicacion"]["lat"]
                item["lon"] = location["ubicacion"]["lng"]
                item["city"] = location["ciudad"]

                apply_category(Categories.FUEL_STATION, item)

                apply_yes_no(Fuel.DIESEL, item, "diesel" in location["tipo"])
                yield item
