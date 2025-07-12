from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_locations import YextLocationsSpider


class CoinflipSpider(YextLocationsSpider):
    name = "coinflip"
    item_attributes = {"brand": "CoinFlip", "brand_wikidata": "Q109850256"}
    api_key = "7ef064ccd105050c8cab5880d6bfefa7"
    api_version = "20231114"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("email", None)

        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        match item.get("country"):
            case "AU":
                item["extras"]["currency:AUD"] = "yes"
            case "BR":
                item["extras"]["currency:BRL"] = "yes"
            case "CA":
                item["extras"]["currency:CAD"] = "yes"
            case "ES" | "IT":
                item["extras"]["currency:EUR"] = "yes"
            case "MX":
                item["extras"]["currency:MXN"] = "yes"
            case "NZ":
                item["extras"]["currency:NZD"] = "yes"
            case "PA" | "PR" | "US":
                item["extras"]["currency:USD"] = "yes"
            case "ZA":
                item["extras"]["currency:ZAR"] = "yes"
            case None:
                pass
            case _:
                self.logger.warning(
                    "ATM is located in country '{}' for which the local currency is undefined by this spider. The spider should be updated to map a currency for this country.".format(
                        item.get("country")
                    )
                )
        item["extras"]["cash_in"] = "yes"
        if location.get("c_oneWayTwoWay") == "ONE-WAY_ATM":
            item["extras"]["cash_out"] = "no"
        else:
            item["extras"]["cash_out"] = "yes"
        yield item
