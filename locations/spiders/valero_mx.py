import re
from typing import Any

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ValeroMXSpider(Spider):
    name = "valero_mx"
    item_attributes = {"brand": "Valero", "brand_wikidata": "Q1283291"}
    start_urls = ["https://www.valero.com.mx/wp-content/themes/VALERO-THEME-2022/estacionesBox/mapa.php"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = response.xpath("//script[contains(text(), 'gasStations')]/text()").get()
        locations_js = re.search(r"gasStations =(.*?)async function", raw_data, re.DOTALL).group(1)
        locations = parse_js_object(locations_js)
        for location in locations:
            item = DictParser.parse(location)
            item["addr_full"] = location["location"]
            item["branch"] = item.pop("name")
            apply_category(Categories.FUEL_STATION, item)
            yield item
