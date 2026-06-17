import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class MtexxBGSpider(Spider):
    name = "mtexx_bg"
    item_attributes = {"operator": "M-Texx", "operator_wikidata": "Q122947768"}
    allowed_domains = ["m-texx.com"]
    start_urls = ["https://m-texx.com/locations"]

    def parse(self, response, **kwargs):
        data_regex = r"<script>self\.__next_f\.push\((.+)?\)<\/script>"
        data_raw = re.search(data_regex, response.text, re.IGNORECASE).group(1)
        data_raw = re.sub(r"\\\"", '"', data_raw)
        cities_raw = re.search(r"\"initialCities\":(.+)?}\],\[", data_raw, re.IGNORECASE).group(1)
        cities = json.loads(cities_raw)
        for city in cities:
            city_name = city["name"]
            for location in city["locations"]:
                properties = {
                    "ref": location["id"],
                    "city": city_name,
                    "addr_full": location["address"],
                    "lat": location["coordinates"][0],
                    "lon": location["coordinates"][1],
                }
                apply_category(Categories.RECYCLING, properties)
                yield Feature(**properties)
