from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.spiders.albertsons import AlbertsonsSpider
from locations.spiders.cumberland_farms_us import CumberlandFarmsUSSpider
from locations.spiders.cvs_us import CVS
from locations.spiders.giant_eagle_us import GiantEagleUSSpider
from locations.spiders.giant_food_us import GiantFoodUSSpider
from locations.spiders.golub_corporation_us import GolubCorporationUSSpider
from locations.spiders.kroger_us import BRANDS as KROGER_BRANDS
from locations.spiders.stop_and_shop_us import StopAndShopUSSpider
from locations.spiders.target_us import TargetUSSpider
from locations.spiders.tops_us import TopsUSSpider
from locations.storefinders.yext import YextSpider


class CitizensUSSpider(YextSpider):
    name = "citizens_us"
    item_attributes = {"brand_wikidata": "Q5122694"}
    api_key = "d4d6be17717272573aeece729fdbec0c"
    wanted_types = ["location", "atm"]

    LOCATED_IN_MAPPINGS = [
        (["CVS"], CVS),
        (["STOP & SHOP", "STOP AND SHOP"], StopAndShopUSSpider.item_attributes),
        (["TARGET"], TargetUSSpider.item_attributes),
        (["KROGER"], KROGER_BRANDS["https://www.kroger.com/"]),
        (["HARRIS TEETER"], KROGER_BRANDS["https://www.harristeeter.com/"]),
        (["CUMBERLAND FARMS"], CumberlandFarmsUSSpider.item_attributes),
        (["GETGO", "GET GO"], GiantEagleUSSpider.GET_GO),
        (["PRICE CHOPPER"], GolubCorporationUSSpider.brands["price-chopper"]),
        (["GIANT"], GiantFoodUSSpider.item_attributes),
        (["GNT EAGLE"], GiantEagleUSSpider.GIANT_EAGLE),
        (["SHAWS"], AlbertsonsSpider.brands["shaws"]),
        (["ACME"], AlbertsonsSpider.brands["acmemarkets"]),
        (["TOPS"], TopsUSSpider.item_attributes),
    ]

    def parse_item(self, item, location):
        if not location.get("c_active", True):
            return
        if "BRANCH" in location.get("c_type", []):
            apply_category(Categories.BANK, item)
            item["ref"] = location.get("c_branchCode", location["meta"].get("id"))
            item["name"] = " ".join(filter(None, [location.get("name"), location.get("geomodifier")]))
        elif "ATM" in location.get("c_type", []):
            apply_category(Categories.ATM, item)
            item.pop("name", None)

            if geomodifier := location.get("geomodifier", ""):
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    geomodifier, self.LOCATED_IN_MAPPINGS, self
                )
        else:
            return
        item.pop("website", None)
        item["extras"].pop("contact:instagram", None)
        item.pop("twitter", None)
        item.pop("facebook", None)
        yield item
