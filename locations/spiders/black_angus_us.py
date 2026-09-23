import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class BlackAngusUSSpider(Spider):
    name = "black_angus_us"
    item_attributes = {"brand": "Black Angus", "brand_wikidata": "Q4920269"}
    start_urls = ["https://www.blackangus.com/locations"]

    def parse(self, response):
        script = response.xpath("//script[contains(text(), 'window.mapData')]/text()").get()
        locations = re.search(r"locations:\s*(\[.*?\]),\s*darkMode:", script, re.S).group(1)

        for location in json.loads(locations):
            item = Feature(
                ref=location["id"],
                branch=location["name"].removeprefix("Black Angus "),
                street_address=location["address"].strip(),
                city=location["city"],
                state=location["state"],
                postcode=location["zip"],
                country="US",
                lat=location["geoLocation"]["latitude"],
                lon=location["geoLocation"]["longitude"],
                phone=location["phone"],
                website=response.urljoin(f"/location/{location['id']}"),
            )
            apply_category(Categories.RESTAURANT, item)
            yield item
