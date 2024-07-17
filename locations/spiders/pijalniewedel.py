import re

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature

ADDRESS_PATTERN = re.compile(r"(?P<street>.*)<br>(?P<postal>[0-9]{2}\s?-\s?[0-9]{3})\s(?P<city>.*)")


class PijalnieWedel(Spider):
    name = "pijalniewedel_pl"
    item_attributes = {
        "brand": "Pijalnia Czekolady E.Wedel",
        "brand_wikidata": "Q1273613",
        "extras": Categories.CAFE.value,
    }
    start_urls = ["https://wedelpijalnie.pl/lokale"]

    def parse(self, response: Response, **kwargs):
        place_data = response.xpath('//script[contains(text(), "var placeData")]/text()').re_first(
            r"var placeData = (.*);"
        )

        place_data = chompjs.parse_js_object(place_data)
        for place in place_data:
            address = ADDRESS_PATTERN.search(place["address"])
            location_div = response.xpath(f"//div[@data-id='{place['slug']}']")

            image_div = location_div.xpath("div[@class='o-location__img ratio']")
            image_url = "https://wedelpijalnie.pl" + image_div.attrib["style"].split("'")[1]

            opening_hours = OpeningHours()
            opening_hours_rows = location_div.xpath(".//div[@class='o-openings__hours-list']/p//text()").getall()
            for opening_day in opening_hours_rows:
                opening_hours.add_ranges_from_string(ranges_string=opening_day, days=DAYS_PL)

            properties = {
                "ref": place["id"],
                "street_address": address["street"],
                "postcode": address["postal"].replace(" ", ""),
                "city": address["city"],
                "lat": place["lat"],
                "lon": place["lng"],
                "phone": location_div.xpath("div/div/a[starts-with(@href,'tel:')]").attrib["href"].removeprefix("tel:"),
                "email": location_div.xpath("div/div/a[starts-with(@href,'mailto:')]")
                .attrib["href"]
                .removeprefix("mailto:"),
                "opening_hours": opening_hours,
                "image": image_url,
            }

            yield Feature(**properties)
