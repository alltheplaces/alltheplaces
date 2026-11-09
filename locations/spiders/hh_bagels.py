from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider

# A shop that has not opened yet is marked as such against this field.
STORE_STATUS = "store status"
NOT_OPEN_YET = "coming soon"


class HhBagelsSpider(StockistSpider):
    """The locator the chain's locations page embeds states all of its shops.

    It carries the shops that have not opened yet alongside the rest, marked
    against a field of their own, and those are not published.

    Each shop also has a page of its own, which states the hours it keeps and
    its telephone number. Those pages are not read: they are written by hand
    and show it, labelling the hours three different ways between them, naming
    a terminal and a food court where the address belongs, and in one case
    stating neither an address nor a number at all. The locator is the orderly
    source and the only one giving coordinates.
    """

    name = "hh_bagels"
    # Neither the chain nor any of its shops has a Wikidata item.
    item_attributes = {"brand": "H&H Bagels"}
    key = "u20410"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        if self.not_open_yet(location):
            self.logger.info(f"{location.get('name')} has not opened yet, so it is not published")
            return

        # Each shop is named for the neighbourhood it stands in.
        item["branch"] = item.pop("name", None)
        # The locator states no country for any of them.
        item["country"] = "US"

        apply_category(Categories.SHOP_BAKERY, item)
        item["extras"]["cuisine"] = "bagel"
        yield item

    @staticmethod
    def not_open_yet(location: dict) -> bool:
        for field in location.get("custom_fields") or []:
            if (field.get("name") or "").strip().casefold() == STORE_STATUS:
                return NOT_OPEN_YET in (field.get("value") or "").casefold()
        return False
