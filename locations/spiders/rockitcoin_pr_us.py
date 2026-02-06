from typing import Iterable

from scrapy.http import Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.ampm_us import AmpmUSSpider
from locations.spiders.bp import BpSpider
from locations.spiders.chevron_us import BRANDS as CHEVRON_BRANDS
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.citgo import CitgoSpider
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.eg_america_us import EgAmericaUSSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.gulf_pr_us import GulfPRUSSpider
from locations.spiders.marathon_petroleum_us import MarathonPetroleumUSSpider
from locations.spiders.phillips_66_conoco_76 import Phillips66Conoco76Spider
from locations.spiders.seven_eleven_ca_us import SevenElevenCAUSSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.valero import ValeroSpider


class RockitcoinPRUSSpider(JSONBlobSpider):
    name = "rockitcoin_pr_us"
    item_attributes = {"brand": "RockItCoin", "brand_wikidata": "Q125924689"}
    allowed_domains = ["us-central1-rockitcoin-data-development.cloudfunctions.net"]
    start_urls = [
        "https://us-central1-rockitcoin-data-development.cloudfunctions.net/rockitcoin-getLocationsHttps?latitude=34.0521&longitude=-118.2436&show2Way=false&showRcGo=true&radiusInM=1000000000000"
    ]
    locations_key = "locations"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    LOCATED_IN_MAPPINGS = [
        (["CVS"], CVS_BRANDS["CVS Pharmacy"]),
        (["SHELL"], ShellSpider.item_attributes),
        (["CHEVRON"], CHEVRON_BRANDS["Chevron"][0]),
        (["BP GAS", "BP"], BpSpider.brands["bp"]),
        (["MARATHON"], MarathonPetroleumUSSpider.brands["MARATHON"]),
        (["ARCO"], MarathonPetroleumUSSpider.brands["ARCO"]),
        (["MOBIL"], ExxonMobilSpider.brands["Mobil"]),
        (["EXXON"], ExxonMobilSpider.brands["Exxon"]),
        (["TEXACO"], CHEVRON_BRANDS["Texaco"][0]),
        (["VALERO"], ValeroSpider.item_attributes),
        (["SUNOCO"], SunocoUSSpider.item_attributes),
        (["CITGO"], CitgoSpider.item_attributes),
        (["76 GAS", "76"], Phillips66Conoco76Spider.BRANDS["76"]),
        (["CIRCLE K", "CIRCLEK"], CircleKSpider.CIRCLE_K),
        (["PHILLIPS 66"], Phillips66Conoco76Spider.BRANDS["P66"]),
        (["7-ELEVEN", "7ELEVEN", "ALON / 7-ELEVEN"], SevenElevenCAUSSpider.item_attributes),
        (["AMPM", "AM/PM"], AmpmUSSpider.item_attributes),
        (["AMOCO"], BpSpider.brands["amoco"]),
        (["RACEWAY"], {"brand": "RaceWay", "brand_wikidata": "Q73039084"}),
        (["CONOCO"], Phillips66Conoco76Spider.BRANDS["CON"]),
        (["GULF"], GulfPRUSSpider.item_attributes),
        (["KWIK SHOP"], EgAmericaUSSpider.brands[18]),
    ]

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

        item["located_in"], item["located_in_wikidata"] = extract_located_in(
            item["name"], self.LOCATED_IN_MAPPINGS, self
        )

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
