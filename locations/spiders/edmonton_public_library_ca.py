import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# A local or former name of the neighbourhood, e.g. "Idylwylde (Bonnie Doon)".
ALTERNATE_NAME_REGEX = re.compile(r"\s*\([^)]*\)$")
HOUSENUMBER_REGEX = re.compile(r"\d+[A-Za-z]?")
# A unit and house number written together, e.g. "160-3210 118 Avenue".
UNIT_AND_HOUSENUMBER_REGEX = re.compile(r"(\d+)-(\d+)")
# A unit and the building it is in, followed by the house number, e.g.
# "106 Lakeside Landing, 15379" with street "Castle Downs Rd".
UNIT_BUILDING_HOUSENUMBER_REGEX = re.compile(r"(\d+)\s+(.+?),?\s+(\d+)")
# A unit and the building it is in, e.g. "145 Whitemud Crossing Shopping
# Centre," where the house number starts the street, "4211 - 106 Street".
UNIT_BUILDING_REGEX = re.compile(r"(\d+)\s+(.+)")
HOUSENUMBER_STREET_REGEX = re.compile(r"(\d+)\s*-?\s*(.+)")


class EdmontonPublicLibraryCASpider(BiblioCommonsSpider):
    name = "edmonton_public_library_ca"
    item_attributes = {"operator": "Edmonton Public Library", "operator_wikidata": "Q5339083"}
    library_id = "epl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Branches are named after their neighbourhood, and the library's
        # display name keeps a local or former name in brackets.
        item["branch"] = branch = item.pop("name")
        item["name"] = "{} Library".format(ALTERNATE_NAME_REGEX.sub("", branch))

        housenumber = (item.get("housenumber") or "").strip(" ,")
        street = (item.get("street") or "").strip(" ,")
        if m := UNIT_AND_HOUSENUMBER_REGEX.fullmatch(housenumber):
            item["unit"], item["housenumber"] = m.group(1), m.group(2)
        elif m := UNIT_BUILDING_HOUSENUMBER_REGEX.fullmatch(housenumber):
            # e.g. unit 106 of Lakeside Landing, house number 15379.
            item["unit"], item["located_in"], item["housenumber"] = m.group(1), m.group(2), m.group(3)
            item["street"] = street.lstrip("- ")
        elif (b := UNIT_BUILDING_REGEX.fullmatch(housenumber)) and (n := HOUSENUMBER_STREET_REGEX.fullmatch(street)):
            if HOUSENUMBER_REGEX.fullmatch(b.group(1)) and not b.group(2)[0].isdigit():
                # e.g. unit 145 of Whitemud Crossing Shopping Centre, house
                # number 4211 of 106 Street.
                item["unit"], item["located_in"] = b.group(1), b.group(2)
                item["housenumber"], item["street"] = n.group(1), n.group(2)
        elif (m := UNIT_BUILDING_REGEX.fullmatch(housenumber)) and not any(c.isdigit() for c in street):
            # e.g. "818 Webber Greens Drive" in West Henday Promenade.
            item["housenumber"], item["street"] = m.group(1), m.group(2)
            item["located_in"] = street
        elif not HOUSENUMBER_REGEX.fullmatch(housenumber) or "," in street:
            # The remaining branches in malls and squares have no house
            # number of their own, e.g. "Suite 166" of "Londonderry Mall".
            item["street_address"] = clean_address(["{} {}".format(housenumber, street).strip()])
            item["housenumber"] = item["street"] = None

        apply_category(Categories.LIBRARY, item)

        yield item
