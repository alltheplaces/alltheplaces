from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider

# Two of the restaurants are listed under the chain's own name rather than a
# name of their own, which is no branch at all.
CHAIN = {"uno pizzeria & grill", "uno pizzeria and grill"}


class UnoPizzeriaAndGrillSpider(StoreRocketSpider):
    """The locator the chain embeds states every one of its restaurants at once.

    Only the restaurants in the United States are in it. The chain also has
    franchises in Saudi Arabia and India, which its locations page names as
    towns and nothing more - no address, no page of their own - so there is
    nothing of them to take.

    The restaurants' own pages are not reachable from here either: the locator
    gives each a slug of its own which matches none of the pages the site
    publishes, so no website is stated rather than a wrong one.
    """

    name = "uno_pizzeria_and_grill"
    item_attributes = {"brand": "Uno Pizzeria & Grill", "brand_wikidata": "Q7897209"}
    storerocket_id = "aDJkm2BpOd"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        name = (item.pop("name", None) or "").strip()
        if name and name.casefold() not in CHAIN:
            item["branch"] = name

        # The locator leaves the country empty for all but one of them.
        item["country"] = "US"

        # Half of the restaurants put something other than an address on the
        # address's second line - a shopping centre, a hotel, the way there
        # from a cross street, or a note to collect the order next door - so
        # only the first line is taken as the street. Any suite number is
        # already stated there.
        item["street_address"] = location.get("address_line_1")
        # The whole address is given in one piece as well, which the parts
        # above already say.
        item.pop("addr_full", None)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"
        yield item
