import json
import re

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class PaczkomatPLSpider(Spider):
    name = "paczkomat_pl"
    item_attributes = {"brand": "Paczkomat", "brand_wikidata": "Q110970254"}
    start_urls = ["https://inpost.pl/sites/default/files/points.json"]

    def parse(self, response, **kwargs):
        for poi in response.json()["items"]:
            # Skip non-active locations
            if poi["s"] != 1:
                continue

            item = Feature()
            item["extras"] = {}
            # The mapping is available in "load" js function of inpostLocatorMap object
            item["ref"] = poi["n"]
            item["name"] = poi["d"]
            item["city"] = poi["c"]
            item["street"] = poi["e"]
            item["state"] = poi["r"]
            item["postcode"] = poi["o"]
            item["housenumber"] = poi["b"]
            item["lat"] = poi["l"]["a"]
            item["lon"] = poi["l"]["o"]

            item["image"] = f'https://geowidget.easypack24.net/uploads/pl/images/{item["ref"]}.jpg'

            item["extras"]["type"] = poi["t"]

            # TODO: figure out if below could be mapped
            # poi["m"]  # apm_doubled
            # poi["q"]  # partner_id
            # poi["f"]  # physical_type_mapped
            # poi["g"]
            # poi["p"]  # payment

            self.parse_slug(item)
            self.parse_hours(item, poi)

            yield item

    def parse_slug(self, item):
        if item["extras"]["type"] == 1:
            slug = "-".join(
                [
                    "paczkomat",
                    item["city"],
                    item["ref"],
                    item["street"],
                    "paczkomaty",
                    item["state"],
                ]
            ).lower()
        else:
            # Code is adapted from js 'getSlug' function
            slug = "-".join(
                [
                    "punkt-obslugi-paczek",
                    item["ref"],
                    item["city"],
                    item["street"],
                ]
            ).lower()
        slug = (
            slug.replace("  ", "")
            .replace("ą", "a")
            .replace("ć", "c")
            .replace("ę", "e")
            .replace("ł", "l")
            .replace("ń", "n")
            .replace("ś", "s")
            .replace("ó", "o")
            .replace("ź", "z")
            .replace("ż", "z")
            .replace("·", "-")
            .replace("/", "-")
            .replace("_", "-")
            .replace(",", "-")
            .replace(":", "-")
            .replace(";", "-")
            .replace(" ", "-")
        )
        slug = re.sub(r"/[^a-z0-9 -]/g", "", slug)
        slug = re.sub(r"/\s+/g", "-", slug)
        slug = re.sub(r"/-+/g", "-", slug)

        item["website"] = f"https://inpost.pl/{slug}"

    def parse_hours(self, item, poi):
        if poi["h"] == "24/7":
            item["opening_hours"] = "24/7"
            return

        if hours := poi.get("i"):
            hours = json.loads(hours)
            if isinstance(hours, list):
                return
            try:
                oh = OpeningHours()
                days_mapping = {
                    "0": "Su",
                    "1": "Mo",
                    "2": "Tu",
                    "3": "We",
                    "4": "Th",
                    "5": "Fr",
                    "6": "Sa",
                }
                for day, range in hours.items():
                    range = [f"{h}:00" if ":" not in h else h for h in range]
                    oh.add_range(days_mapping.get(day), range[0], range[1])
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours {hours}: {e}")
