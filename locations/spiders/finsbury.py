import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature


class FinsburySpider(Spider):
    name = "finsbury"
    item_attributes = {"brand": "Finsbury", "brand_wikidata": "Q141242163", "name": "Finsbury"}
    start_urls = ["https://www.finsbury-shoes.com/pages/nos-boutiques"]

    # These two are mislabelled "France" on the source page despite their address
    # and coordinates clearly being elsewhere.
    COUNTRY_OVERRIDES = {"store_188209135953": "HK", "store_188209791313": "LU"}
    COUNTRY_MAPPING = {
        "France": "FR",
        "Belgique": "BE",
        "Maroc": "MA",
        "Algérie": "DZ",
        "Luxembourg": "LU",
        "Guadeloupe": "GP",
        "Côte d'Ivoire": "CI",
    }
    # Overseas French departments are all labelled "France" here (unlike Guadeloupe
    # above) - postcode prefix reliably tells them apart.
    OVERSEAS_FRANCE_POSTCODES = {
        "971": "GP",
        "972": "MQ",
        "973": "GF",
        "974": "RE",
        "975": "PM",
        "976": "YT",
    }

    def parse(self, response):
        for template in response.css('template[name^="store_"]'):
            store_id = template.attrib["name"]
            block = response.css(f'.map-place-list__list-store[map-target="{store_id}"]')

            item = Feature()
            item["ref"] = store_id
            item["lat"] = template.attrib.get("latitude")
            item["lon"] = template.attrib.get("longitude")
            item["branch"] = block.css(".map-place-list__list-store-name::text").get("").strip()
            item["street_address"] = block.css(".map-place-list__list-address::text").get("").strip()

            # Address city block is "<postcode>\xa0<city>"; either half can be
            # missing on a handful of entries, so guess which token is which.
            city_line = block.css(".map-place-list__list-address-city::text").get("").replace("\xa0", " ").strip()
            postcode, _, city = city_line.partition(" ")
            if postcode and not postcode[0].isdigit():
                postcode, city = "", city_line
            item["postcode"] = postcode
            item["city"] = city

            country = block.css(".map-place-list__list-address-country::text").get("").strip()
            item["country"] = self.COUNTRY_OVERRIDES.get(store_id) or self.COUNTRY_MAPPING.get(country, country)
            if item["country"] == "FR" and postcode:
                item["country"] = self.OVERSEAS_FRANCE_POSTCODES.get(postcode[:3], item["country"])

            # A handful of stores cram a second phone number, or even an email,
            # into this same field separated by " - " instead of a proper list.
            if href := block.css(".map-place-list__list-store-contacts a::attr(href)").get():
                parts = [p.strip() for p in href.removeprefix("callto:").split(" - ")]
                if phones := [p for p in parts if "@" not in p]:
                    item["phone"] = "; ".join(phones)
                if emails := [p for p in parts if "@" in p]:
                    item["email"] = emails[0]

            if hours := block.css(".map-place-list__list-store-opening-hours").get():
                oh = OpeningHours()
                hours = hours.replace("<br>", "\n").replace("<br/>", "\n")
                # A split lunch-break shift joins its two ranges with "et"/"puis"
                # rather than the comma the day-range regex expects.
                hours = re.sub(r"\s+(?:et|puis)\s+", ",", hours, flags=re.IGNORECASE)
                oh.add_ranges_from_string(hours, days=DAYS_FR, delimiters=DELIMITERS_FR, closed=CLOSED_FR)
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_SHOES, item)
            yield item
