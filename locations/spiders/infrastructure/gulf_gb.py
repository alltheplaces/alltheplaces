import re

import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class GulfGBSpider(scrapy.Spider):
    name = "gulf_gb"
    start_urls = ["https://gulfoil.co.uk/find-your-nearest-gulf-station/"]
    item_attributes = {"brand": "Gulf", "brand_wikidata": "Q5617505"}

    def parse(self, response):
        script_text = response.xpath('//script[contains(text(), "var settings")]/text()').get()
        if not script_text:
            return

        match = re.search(r"var settings = ({.*?});", script_text, re.DOTALL)
        if not match:
            return

        settings = chompjs.parse_js_object(match.group(1))
        pins = settings.get("pins", {}).get("pins", [])

        for location in pins:
            item = Feature()
            item["ref"] = location.get("id")
            item["branch"] = location.get("title")
            item["lat"] = location.get("latlng", [])[0]
            item["lon"] = location.get("latlng", [])[1]
            item["city"] = location.get("city")
            item["postcode"] = location.get("zip")

            apply_category(Categories.FUEL_STATION, item)

            yield item
