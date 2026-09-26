import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class CzystoPLSpider(scrapy.Spider):
    name = "czysto_pl"
    item_attributes = {
        "brand": "czysto.pl",
        "brand_wikidata": "Q128605367",
        "name": "czysto.pl",
    }
    start_urls = ["https://czysto.pl/nasze-myjnie/"]

    def parse(self, response):
        # The store finder page embeds a JS array of markers, each linking to a
        # per-location detail page (which has the full address and true lat/lon).
        seen = set()
        for location_id in re.findall(r'href="/podglad-myjni/\?id=(\d+)"', response.text):
            if location_id in seen:
                continue
            seen.add(location_id)
            yield scrapy.Request(
                f"https://czysto.pl/podglad-myjni/?id={location_id}",
                cb_kwargs={"ref": location_id},
                callback=self.parse_location,
            )

    def parse_location(self, response, ref):
        item = Feature()
        item["ref"] = ref
        item["website"] = response.url
        item["country"] = "PL"

        item["branch"] = " ".join(response.css(".cw_info h1::text").get("").split())

        if address := self.extract_field(response.text, "Adres"):
            item["addr_full"] = address
            if m := re.match(r"(.+?),\s*(\d{2}-\d{3})\s+(.+)", address):
                item["street_address"] = m.group(1).strip()
                item["postcode"] = m.group(2)
                item["city"] = m.group(3).strip()

        item["phone"] = self.extract_field(response.text, "Telefon")
        item["email"] = self.extract_field(response.text, "E-mail")

        # Coordinates come from the per-location embedded Google Maps JS
        # initialiser, which the site populates with its own known pin
        # location (not a geocoded place/search link).
        if m := re.search(r"lat:\s*(-?\d+\.\d+),\s*lng:\s*(-?\d+\.\d+)", response.text):
            item["lat"] = float(m.group(1))
            item["lon"] = float(m.group(2))

        apply_category(Categories.CAR_WASH, item)

        yield item

    @staticmethod
    def extract_field(text: str, label: str) -> str | None:
        if m := re.search(rf"{label}:\s*</strong>\s*([^<]*)", text):
            return " ".join(m.group(1).split()) or None
        return None
