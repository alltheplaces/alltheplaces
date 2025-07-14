from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class UnbankUSSpider(JSONBlobSpider):
    name = "unbank_us"
    item_attributes = {"brand": "Unbank", "brand_wikidata": "Q126894750"}
    allowed_domains = ["web.unbankworld.com"]
    start_urls = ["https://web.unbankworld.com/api/resources/atm/bst?buy_or_sell=all&is_batm=1&limit=10000"]
    locations_key = "rows"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("visible_on_website") != "1":
            return

        item["ref"] = feature["entity_id"]
        item["located_in"] = feature["name"]
        item.pop("name", None)
        item["website"] = "https://unbank.com/locations/atms/" + feature["slug"]

        apply_category(Categories.ATM, item)
        currencies_map = {
            "BTC": "XBT",
            "DOGE": "DOGE",
            "ETH": "ETH",
            "LTC": "LTC",
            "USDT": "USDT",
        }
        for currency in feature.get("purchase_minimum").keys():
            if currency not in currencies_map.keys():
                self.logger.warning(
                    "Unknown cryptocurrency '{}'. Cryptocurrency tags ignored. Spider requires update to map to correct OSM currency:* key.".format(
                        currency
                    )
                )
                continue
            osm_currency_code = currencies_map[currency]
            item["extras"][f"currency:{osm_currency_code}"] = "yes"
        item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"

        yield item
