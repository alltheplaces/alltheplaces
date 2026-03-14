from typing import AsyncIterator

from scrapy.http import Request

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.astron_energy_za import AstronEnergyZASpider
from locations.spiders.bp import BpSpider
from locations.spiders.builders import BuildersSpider
from locations.spiders.caltex import CaltexSpider
from locations.spiders.chicken_licken import ChickenLickenSpider
from locations.spiders.edgars import EdgarsSpider
from locations.spiders.engen import EngenSpider
from locations.spiders.food_lovers_market_za import FOOD_LOVERS_STORE_TYPES
from locations.spiders.freshstop_za import FreshstopZASpider
from locations.spiders.game_za import GameZASpider
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.spiders.ok_foods import OK_FOODS_BRANDS
from locations.spiders.pep import PepSpider
from locations.spiders.sasol_za import SasolZASpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.shell import ShellSpider
from locations.spiders.shoprite_holdings import SHOPRITE_BRANDS
from locations.spiders.spar_bw_mz_na_sz_za import BRANDS as SPAR_BRANDS
from locations.spiders.total_energies import TotalEnergiesSpider
from locations.spiders.tymebank_za import PICK_N_PAY_BRANDS
from locations.spiders.woolworths_za import WoolworthsZASpider

LOCATED_IN_MAPPINGS = [
    (["7-11", "7/11", "7-ELEVEN"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
    (["FRESHSTOP", "FRESH STOP"], FreshstopZASpider.item_attributes),
    (["SHOPRITE"], SHOPRITE_BRANDS["Shoprite"]),
    (["CHECKERS"], SHOPRITE_BRANDS["Checkers"]),
    (["SUPERSPAR"], SPAR_BRANDS["SUPERSPAR"][1]),
    (["KWIKSPAR", "KWIK SPAR"], SPAR_BRANDS["KWIKSPAR"][1]),
    (["SPAR"], SPAR_BRANDS["SPAR"][1]),
    (["SAVEMOR"], SPAR_BRANDS["Savemor"][1]),
    (["PNP", "PICK N PAY"], PICK_N_PAY_BRANDS["PNP"]),
    (["BOXER"], PICK_N_PAY_BRANDS["BOXER"]),
    (["WOOLWORTHS"], WoolworthsZASpider.item_attributes),
    (["GAME"], GameZASpider.item_attributes),
    (["BUILDERS"], BuildersSpider.item_attributes),
    (["U-SAVE", "USAVE", "U SAVE"], SHOPRITE_BRANDS["Usave"]),
    (["OK GROCER"], OK_FOODS_BRANDS["OK GROCER"]),
    (["OK FOODS"], OK_FOODS_BRANDS["OK FOODS"]),
    (["OK MINIMARK", "OK MINI"], OK_FOODS_BRANDS["OK MINIMARK"]),
    (["OK VALUE"], OK_FOODS_BRANDS["OK VALUE"]),
    (["OK "], OK_FOODS_BRANDS["OK FOODS"]),
    (["CAMBRIDGE"], {"brand": "Cambridge Food", "brand_wikidata": "Q129263104"}),
    (["FOOD LOVER"], FOOD_LOVERS_STORE_TYPES["Store"]),
    (["PEP "], {"brand": PepSpider.brands["PEP"][0], "brand_wikidata": PepSpider.brands["PEP"][1]}),
    (["EDGARS"], EdgarsSpider.item_attributes),
    (["CHICKEN LICKEN"], ChickenLickenSpider.item_attributes),
    (["KFC"], KFC_SHARED_ATTRIBUTES),
    (["ENGEN"], EngenSpider.item_attributes),
    (["SHELL"], ShellSpider.item_attributes),
    (["CALTEX"], CaltexSpider.item_attributes),
    (["BP "], BpSpider.brands["bp"]),
    (["TOTAL"], TotalEnergiesSpider.BRANDS["tot"]),
    (["SASOL"], SasolZASpider.item_attributes),
    (["ASTRON"], AstronEnergyZASpider.item_attributes),
]

FACILITIES_MAP = {
    "Deposit Taking ATM": Extras.ATM,
    "Non-Deposit Taking ATM": Extras.ATM,
    "Wheel Chair Friendly": Extras.WHEELCHAIR,
    "Wheel Chair Friendly with Staff Assistance*": Extras.WHEELCHAIR_LIMITED,
    "Wi-Fi": Extras.WIFI,
}
NEDBANK_SHARED_ATTRIBUTES = {
    "brand": "Nedbank",
    "brand_wikidata": "Q2751701",
}


class NedbankZASpider(JSONBlobSpider):
    name = "nedbank_za"
    item_attributes = NEDBANK_SHARED_ATTRIBUTES
    start_urls = ["https://personal.nedbank.co.za/contact/find-us.html"]
    locations_key = "data"

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_json)

    def fetch_json(self, response):
        auth_token = response.xpath('.//input[@id="authorizationtoken"]/@value').get()
        yield Request(
            url="https://api.nedsecure.co.za/nedbank/channeldistribution/v2/branches?resultsize=1000&latitude=-26&longitude=28",
            headers={"Authorization": f"Bearer {auth_token}"},
            callback=self.parse,
            meta={"auth_token": auth_token},
        )
        yield Request(
            url="https://api.nedsecure.co.za/nedbank/channeldistribution/v2/atms?resultsize=10000&latitude=-26&longitude=28",
            headers={"Authorization": f"Bearer {auth_token}"},
            callback=self.parse,
        )

    def pre_process_data(self, location):
        if "geoLocation" in location:
            location.update(location.pop("geoLocation"))
        if "address" in location:
            location.update(location.pop("address"))

    def post_process_item(self, item, response, location):
        if location["type"] in ["ATM", "ID"]:  # ID = Intelligent Depositor (deposit-capable ATM)
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, location.get("depositIndicator") == "YES")
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                item.get("name", ""), LOCATED_IN_MAPPINGS, self
            )
            yield item
        elif location["type"] == "Physical Branch":
            apply_category(Categories.BANK, item)
            item["ref"] = location["code"]
            facilities = [facility["name"] for facility in location["facilities"]]
            for facility in facilities:
                if match := FACILITIES_MAP.get(facility):
                    apply_yes_no(match, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_facility/{facility}")
            if "Wheel Chair Friendly with Staff Assistance*" in facilities:
                item["extras"]["wheelchair:description"] = "With staff assistance"
            item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
            yield Request(
                url=f"https://api.nedsecure.co.za/nedbank/channeldistribution/v2/branches/{item['ref']}",
                headers={"Authorization": f"Bearer {response.meta['auth_token']}"},
                meta={"item": item},
                callback=self.parse_store,
            )
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_type/{location['type']}")

    def parse_store(self, response):
        item = response.meta["item"]
        location = response.json()["data"]
        item["opening_hours"] = OpeningHours()
        for day_hours in location["businessHours"]:
            if day_hours["openingHour"].lower() == "closed":
                item["opening_hours"].set_closed(day_hours["day"])
            else:
                item["opening_hours"].add_range(day_hours["day"], day_hours["openingHour"], day_hours["closingHour"])
        yield item
