import json
from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class HarmonieMutuelleFRSpider(Spider):
    name = "harmonie_mutuelle_fr"
    item_attributes = {"brand": "Harmonie Mutuelle", "brand_wikidata": "Q3127528"}
    # The store finder at agences.harmonie-mutuelle.fr loads its data from this Drupal API.
    # A search with a very large radius returns every agency.
    start_urls = [
        "https://main-bvxea6i-hlf7gnmlsavsw.eu-5.platformsh.site/hm-parcours-web-store-locator/agencies/search/Paris?distance=20000&isOpenedSaturday=false"
    ]
    # The API host is a platform.sh environment, which serves a robots.txt that disallows everything.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    day_fields = {
        "Mo": "field_monday_opening",
        "Tu": "field_tuesday_opening",
        "We": "field_opening_wednesday",
        "Th": "field_opening_thursday",
        "Fr": "field_opening_friday",
        "Sa": "field_opening_saturday",
        "Su": "field_opening_sunday",
    }

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for agency in response.json():
            if self.value(agency, "field_definitive_closure"):
                continue

            item = Feature()
            item["ref"] = self.value(agency, "nid")
            item["lat"] = self.value(agency, "field_latitude")
            item["lon"] = self.value(agency, "field_longitude")
            # The title reads "City - street address" and is cleaner than the street field.
            city, _, street_address = self.value(agency, "title").partition(" - ")
            item["street_address"] = " ".join(street_address.split()) or self.value(agency, "field_address_street")
            item["city"] = self.value(agency, "field_ville") or city.strip()
            item["postcode"] = self.value(agency, "field_address_postal_code")
            if path := (agency.get("path") or [{}])[0].get("alias"):
                item["website"] = urljoin("https://agences.harmonie-mutuelle.fr", path)

            try:
                item["opening_hours"] = self.parse_opening_hours(agency)
            except Exception:
                pass

            apply_category(Categories.OFFICE_INSURANCE, item)
            yield item

    def parse_opening_hours(self, agency: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, field in self.day_fields.items():
            hours = json.loads(self.value(agency, field) or "{}")
            if not isinstance(hours, dict):
                continue
            for time_range in hours.values():
                # Most ranges look like "09:00-12:30", a few use "09h00 - 12h30".
                start_time, end_time = time_range.replace(" ", "").replace("h", ":").split("-")
                if start_time != end_time:
                    oh.add_range(day, start_time, end_time)
        return oh

    @staticmethod
    def value(agency: dict, field: str) -> str | None:
        values = agency.get(field) or [{}]
        return values[0].get("value")
