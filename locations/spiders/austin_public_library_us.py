import re
from datetime import datetime, timezone
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.drupal_json_api import DrupalJsonApiSpider, parse_office_hours

# e.g. "(30.269564600000, -97.724043800000)"
LAT_LON_REGEX = re.compile(r"\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)")


class AustinPublicLibraryUSSpider(DrupalJsonApiSpider):
    name = "austin_public_library_us"
    item_attributes = {"operator": "Austin Public Library", "operator_wikidata": "Q69491633"}
    drupal_host = "https://library.austintexas.gov"
    jsonapi_resource = "taxonomy_term/library_location"

    async def start(self) -> AsyncIterator[JsonRequest]:
        self.hours = {}
        yield self.make_request("node/open_hours", callback=self.parse_hours)

    async def parse_hours(self, response: TextResponse) -> AsyncIterator[JsonRequest]:
        # Each location has a history of overlapping hours records. The site
        # shows the one whose "slr" window covers now and began most recently;
        # field_effective_date is much wider and picks stale closures.
        now = datetime.now(timezone.utc)
        for record in response.json().get("data") or []:
            attributes = record.get("attributes") or {}
            start, end = attributes.get("field_slr_time_start"), attributes.get("field_slr_time_end")
            if not start or not end:
                continue
            start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
            if not start <= now <= end:
                continue
            locations = ((record.get("relationships") or {}).get("field_location") or {}).get("data") or []
            for location in locations:
                current = self.hours.get(location.get("id"))
                if current is None or start > current[0]:
                    self.hours[location.get("id")] = (start, attributes.get("field_open_hours__") or [])

        if next_page := self.next_page(response):
            yield JsonRequest(url=next_page, callback=self.parse_hours)
        else:
            async for request in super().start():
                yield request

    def post_process_item(self, item: Feature, response: TextResponse, entry: dict, **kwargs) -> Iterable[Feature]:
        attributes = entry.get("attributes") or {}
        # Only library outlets have an ILS location code. This drops the APL
        # Shop inside Central, the Mobile Library, "Online Event", the Recycled
        # Reads bookstore (closed January 2026) and the African American
        # Cultural and Heritage Facility, which the city's arts office runs.
        if not attributes.get("field_location_code"):
            return

        item["branch"] = item.pop("name")
        if item["branch"] == "Central Library":
            item["name"] = "Austin Central Library"
        else:
            item["name"] = "Austin Public Library - {}".format(item["branch"].removesuffix(", Faulk Building"))

        item["street_address"] = attributes.get("field_street_address")
        item["postcode"] = attributes.get("field_zipcode")
        item["phone"] = attributes.get("field_phone_num")
        if m := LAT_LON_REGEX.fullmatch((attributes.get("field_latitude_longitude") or "").strip()):
            item["lat"], item["lon"] = m.group(1), m.group(2)

        if (hours := self.hours.get(entry.get("id"))) is not None:
            if slots := hours[1]:
                item["opening_hours"] = parse_office_hours(slots)
            else:
                # A current record with no times is a closure, e.g. Old Quarry
                # and Willie Mae Kirk during renovation.
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].set_closed(DAYS)

        apply_category(Categories.LIBRARY, item)
        yield item
