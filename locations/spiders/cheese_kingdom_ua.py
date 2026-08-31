import re
from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class CheeseKingdomUASpider(Spider):
    name = "cheese_kingdom_ua"
    item_attributes = {"brand": "Сирне королівство", "brand_wikidata": "Q123748624"}
    start_urls = ["https://cheesekingdom.com.ua/en/contact-us/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # City names used as keys in the "addresses" blob are Ukrainian; the city
        # picker's <option> elements give us the matching English name.
        city_names = {
            option.xpath("@value").get(): option.xpath("text()").get()
            for option in response.xpath('//select[@id="citySelect"]/option[@value!=""]')
        }

        # Store data is a JS object literal (not strict JSON) embedded in a
        # <script> block: `const addresses = {"<city>": [{address, text, image}, ...], ...};`
        js_text = response.text[response.text.index("const addresses = ") + len("const addresses = ") :]
        addresses = chompjs.parse_js_object(js_text)

        for city, locations in addresses.items():
            for location in locations:
                yield from self.parse_location(city_names.get(city, city), location)

    def parse_location(self, city: str, location: dict) -> Any:
        item = Feature(
            {
                "ref": f"{city}: {location['address']}",
                "addr_full": ", ".join([location["address"], city, "Ukraine"]),
                "city": city,
                "country": "UA",
                "website": "https://cheesekingdom.com.ua/en/contact-us/",
            }
        )

        details = Selector(text=location["text"])
        full_text = " ".join(t.strip() for t in details.xpath("//text()").getall() if t.strip())

        if phone := re.search(r"tel:(\+?\d+)", location["text"]):
            item["phone"] = phone.group(1)

        if hours := re.search(r"Working hours:?\s*(.+?)\s*Phone number", full_text):
            oh = OpeningHours()
            oh.add_ranges_from_string(hours.group(1))
            item["opening_hours"] = oh

        # The store finder's Google Maps links are place/search links (a geocode
        # result derived from Google resolving an address), not embeds, so no
        # reliable coordinate can be taken from them.

        apply_category(Categories.SHOP_CHEESE, item)

        yield item
