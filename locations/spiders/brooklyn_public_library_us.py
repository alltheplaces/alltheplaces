import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.drupal_json_api import DrupalJsonApiSpider

# e.g. "2636 E. 14th St. at Ave. Z", "6802 Fort Hamilton Pkwy (at 68th St.)"
CROSS_STREET_REGEX = re.compile(r"\s*\([^)]*\)|\s+at\s+.*$")


class BrooklynPublicLibraryUSSpider(DrupalJsonApiSpider):
    name = "brooklyn_public_library_us"
    item_attributes = {"operator": "Brooklyn Public Library", "operator_wikidata": "Q1198796"}
    drupal_host = "https://www.bklynlibrary.org"
    jsonapi_resource = "node/branch"
    address_field = "field_address"
    geofield_field = "field_position"
    # robots.txt asks all user agents for a 30 second crawl delay.
    custom_settings = {"DOWNLOAD_DELAY": 30}

    def post_process_item(self, item: Feature, response: TextResponse, entry: dict, **kwargs) -> Iterable[Feature]:
        attributes = entry.get("attributes") or {}
        branch_id = attributes.get("field_branchid") or ""
        # No branch code: the Kidsmobile bookmobile and the Central Library
        # Youth Wing. Codes ending "L" are adult learning centers inside
        # branches, 777 is the Teen Tech Center and 408 is the Othmer Library
        # inside the Center for Brooklyn History.
        if not branch_id or branch_id.endswith("L") or branch_id in ("777", "408"):
            return

        if (item.get("name") or "").endswith(" Library"):
            item["branch"] = item["name"].removesuffix(" Library")
        if item.get("street_address"):
            item["street_address"] = CROSS_STREET_REGEX.sub("", item["street_address"])
        item["phone"] = attributes.get("field_branch_phone")

        oh = OpeningHours()
        if attributes.get("field_branch_status") == 3:
            # Status 3 is "closed for renovations", where the weekly hours are
            # left as they were before closing.
            oh.set_closed(DAYS_FULL)
        else:
            for day in DAYS_FULL:
                hours = attributes.get("field_hours_{}".format(day.lower())) or {}
                if hours.get("from") is None or hours.get("to") is None:
                    oh.set_closed(day)
                else:
                    oh.add_range(
                        day,
                        "{:02}:{:02}".format(*divmod(hours["from"] // 60, 60)),
                        "{:02}:{:02}".format(*divmod(hours["to"] // 60, 60)),
                    )
        item["opening_hours"] = oh

        # Shown on branch pages as "Fully accessible" (0), "Partially
        # accessible" (1) and "Not accessible" (2).
        access = attributes.get("field_branch_handicap_access")
        apply_yes_no(Extras.WHEELCHAIR, item, access == 0)
        apply_yes_no(Extras.WHEELCHAIR_LIMITED, item, access == 1)
        apply_yes_no(Extras.WIFI, item, attributes.get("field_branch_wifi"))
        apply_yes_no(Extras.TOILETS, item, attributes.get("field_branch_bathrooms"))
        apply_yes_no(Extras.OUTDOOR_SEATING, item, attributes.get("field_outdoor_seating"))
        apply_yes_no(Extras.PRINTING, item, attributes.get("field_print_anywhere"))

        apply_category(Categories.LIBRARY, item)

        yield item
