from typing import Iterable

from scrapy.http import Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.bp import BpSpider
from locations.spiders.chevron_us import BRANDS as CHEVRON_BRANDS
from locations.spiders.citgo import CitgoSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.gulf_pr_us import GulfPRUSSpider
from locations.spiders.marathon_petroleum_us import MarathonPetroleumUSSpider
from locations.spiders.phillips_66_conoco_76 import Phillips66Conoco76Spider
from locations.spiders.shell import ShellSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.valero import ValeroSpider


class UnbankUSSpider(JSONBlobSpider):
    name = "unbank_us"
    item_attributes = {"brand": "Unbank", "brand_wikidata": "Q126894750"}
    allowed_domains = ["web.unbankworld.com"]
    start_urls = ["https://web.unbankworld.com/api/resources/atm/bst?buy_or_sell=all&is_batm=1&limit=10000"]
    locations_key = "rows"

    LOCATED_IN_MAPPINGS = [
        (["SHELL"], ShellSpider.item_attributes),
        (["SUNOCO"], SunocoUSSpider.item_attributes),
        (["EXXON"], ExxonMobilSpider.brands["Exxon"]),
        (["MOBIL"], ExxonMobilSpider.brands["Mobil"]),
        (["CONOCO"], Phillips66Conoco76Spider.BRANDS["CON"]),
        (["PHILLIPS 66"], Phillips66Conoco76Spider.BRANDS["P66"]),
        (["76"], Phillips66Conoco76Spider.BRANDS["76"]),
        (["BP"], BpSpider.brands["bp"]),
        (["AMOCO"], BpSpider.brands["amoco"]),
        (["CHEVRON"], CHEVRON_BRANDS["Chevron"][0]),
        (["TEXACO"], CHEVRON_BRANDS["Texaco"][0]),
        (["VALERO"], ValeroSpider.item_attributes),
        (["MARATHON"], MarathonPetroleumUSSpider.brands["MARATHON"]),
        (["ARCO"], MarathonPetroleumUSSpider.brands["ARCO"]),
        (["CITGO"], CitgoSpider.item_attributes),
        (["GULF"], GulfPRUSSpider.item_attributes),
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("visible_on_website") != 1:
            return

        item["ref"] = feature["entity_id"]
        located_in_name = feature["name"]
        item["located_in"], item["located_in_wikidata"] = extract_located_in(
            located_in_name or "", self.LOCATED_IN_MAPPINGS, self
        )
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
