import json
import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser


class EkoGRSpider(Spider):
    name = "eko_gr"
    item_attributes = {"brand": "EKO", "brand_wikidata": "Q31283948", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.eko.gr"]
    start_urls = ["https://www.eko.gr/pratiria/katastimata/"]

    def parse(self, response: Response):
        if match := re.search(r"Alpine\.store\('gas_stations'\)\.set\((\{.*?\})\)", response.text, re.DOTALL):
            data = json.loads(match.group(1))
            services = {s["term_id"]: s["name"] for s in data.get("services", [])}

            for station in data.get("stations", []):
                item = DictParser.parse(station)

                if coords := station.get("coordinates"):
                    item["lon"] = coords[0]
                    item["lat"] = coords[1]

                if phones := station.get("phones"):
                    item["phone"] = "; ".join(p["phone"] for p in phones if p.get("phone"))

                station_services = [services.get(s) for s in station.get("services", [])]
                apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in station_services, False)
                apply_yes_no(Extras.WIFI, item, "WiFi" in station_services, False)

                yield item
