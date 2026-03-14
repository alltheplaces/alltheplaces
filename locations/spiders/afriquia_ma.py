import re

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class AfriquiaMASpider(Spider):
    name = "afriquia_ma"
    item_attributes = {"brand": "Afriquia افريقيا", "brand_wikidata": "Q56300032"}
    start_urls = ["https://www.afriquia.ma/reseau/stations-services"]

    def parse(self, response: Response):
        js_data = response.xpath('//script[contains(text(), "places = [")]/text()').get()
        if not js_data:
            return

        places_match = re.search(r"places = (\[.*?\]);", js_data, re.DOTALL)
        if not places_match:
            return

        for place in chompjs.parse_js_object(places_match.group(1)):
            path = place[5].replace("?tmpl=component", "")
            properties = {
                "lat": place[1],
                "lon": place[2],
                "name": place[7],
                "ref": path.split("/")[-1],
                "website": "https://www.afriquia.ma" + path,
            }

            address_match = re.search(r"<p class='adresse'>(.*?)</p>", place[4], re.DOTALL)
            if address_match:
                address_parts = [
                    p for p in (p.strip() for p in address_match.group(1).replace("<br />", "\n").split("\n")) if p
                ]
                if len(address_parts) >= 2:
                    properties["city"] = address_parts[-1]
                    properties["street_address"] = ", ".join(address_parts[:-1])
                elif len(address_parts) == 1:
                    properties["addr_full"] = address_parts[0]

            apply_category(Categories.FUEL_STATION, properties)
            yield Feature(**properties)
