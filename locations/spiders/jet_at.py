import re
from typing import Any

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class JetATSpider(Spider):
    name = "jet_at"
    item_attributes = {"brand": "Jet", "brand_wikidata": "Q568940"}
    start_urls = ["https://www.jet-austria.at/tankstellen-suche?"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = response.xpath('//script[contains(text(), "const globals")]').get()
        locations = parse_js_object(re.search(r"stationsData:(.*?)};", raw_data, re.DOTALL).group(1))
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["publicId"]
            item["branch"] = location["operatorName"]
            item["street_address"] = item.pop("street")
            item["website"] = location["webUrl"]

            apply_category(Categories.FUEL_STATION, item)
            yield item
