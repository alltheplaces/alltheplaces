import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

POSTCODE_REGEX = re.compile(r"\s*,?\s*(\d{5})$")


class DenverPublicLibraryUSSpider(Spider):
    name = "denver_public_library_us"
    item_attributes = {"operator": "Denver Public Library", "operator_wikidata": "Q5259775", "state": "CO"}
    # The branch proximity view lists every location with the coordinates from
    # its Drupal geolocation field, which the plain /locations listing lacks.
    start_urls = ["https://www.denverlibrary.org/location_proximity"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.css(".geolocation-location"):
            item = Feature()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()

            path = location.css(".views-field-title a::attr(href)").get() or ""
            item["ref"] = path.removeprefix("/content/").strip("/")
            item["website"] = response.urljoin(path)

            name = " ".join((location.css(".views-field-title a::text").get() or "").split())
            if name == "Central Library":
                # The Central Library building is signed with the system name.
                item["branch"] = name
                item["name"] = "Denver Public Library"
            else:
                item["name"] = name

            address = " ".join((location.css(".views-field-field-address").xpath("string(.)").get() or "").split())
            if postcode := POSTCODE_REGEX.search(address):
                item["postcode"] = postcode.group(1)
                address = address[: postcode.start()]
            item["street_address"] = address.rstrip(" ,")
            # The address gives only street and postcode; every branch is in Denver.
            item["city"] = "Denver"

            item["phone"] = location.css(".views-field-field-phone .field-content::text").get()

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                hours = location.css(f".views-field-field-{day.lower()}-branch .field-content::text").get()
                if hours := " ".join((hours or "").split()):
                    # e.g. "10 a.m.-6 p.m." or "Closed" while a branch is
                    # closed for renovation.
                    item["opening_hours"].add_ranges_from_string(f"{day}: {hours}")

            apply_category(Categories.LIBRARY, item)
            yield item
