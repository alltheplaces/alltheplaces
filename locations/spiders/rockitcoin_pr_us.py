from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.cvs_us import CVS


class RockitcoinPRUSSpider(JSONBlobSpider):
    name = "rockitcoin_pr_us"
    item_attributes = {"brand": "RockItCoin", "brand_wikidata": "Q125924689"}
    allowed_domains = ["us-central1-rockitcoin-data-development.cloudfunctions.net"]
    start_urls = [
        "https://us-central1-rockitcoin-data-development.cloudfunctions.net/rockitcoin-getLocationsHttps?latitude=34.0521&longitude=-118.2436&show2Way=false&showRcGo=true&radiusInM=1000000000000"
    ]
    locations_key = "locations"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["addr_full"].endswith("Puerto Rico"):
            item["country"] = "PR"
        elif item["addr_full"].endswith("USA"):
            item["country"] = "US"

        if hours_string := feature.get("hours"):
            item["opening_hours"] = OpeningHours()
            if hours_string == "Open 24/7":
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                item["opening_hours"].add_ranges_from_string(hours_string)

        if feature["id"].startswith("CVS"):
            item["located_in"] = CVS["brand"]
            item["located_in_wikidata"] = CVS["brand_wikidata"]

        apply_category(Categories.ATM, item)
        item["extras"]["currency:USD"] = "yes"
        currencies_for_buying = [currency["code"] for currency in feature.get("crypto") if currency["buy"] == "1"]
        currencies_for_selling = [currency["code"] for currency in feature.get("crypto") if currency["buy"] == "1"]
        all_currencies = list(set(currencies_for_buying + currencies_for_selling))
        currencies_map = {
            "BCH": "BCH",
            "BTC": "XBT",
            "DASH": "DASH",
            "ETH": "ETH",
            "LTC": "LTC",
        }
        for currency in all_currencies:
            if currency not in currencies_map.keys():
                self.logger.warning(
                    "Unknown cryptocurrency '{}'. Cryptocurrency tags ignored. Spider requires update to map to correct OSM currency:* key.".format(
                        currency
                    )
                )
                continue
            osm_currency_code = currencies_map[currency]
            item["extras"][f"currency:{osm_currency_code}"] = "yes"
        if len(currencies_for_buying) > 0:
            item["extras"]["cash_in"] = "yes"
        if len(currencies_for_selling) > 0:
            item["extras"]["cash_out"] = "yes"

        yield item
