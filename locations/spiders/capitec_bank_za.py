from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.alpha_pharm_za import AlphaPharmZASpider
from locations.spiders.bp import BpSpider
from locations.spiders.buildit import BuilditSpider
from locations.spiders.caltex import CaltexSpider
from locations.spiders.engen import EngenSpider
from locations.spiders.food_lovers_market_za import FOOD_LOVERS_STORE_TYPES
from locations.spiders.freshstop_za import FreshstopZASpider
from locations.spiders.game_za import GameZASpider
from locations.spiders.metro_cash_and_carry import MetroCashAndCarrySpider
from locations.spiders.ok_foods import OK_FOODS_BRANDS
from locations.spiders.ok_furniture import OkFurnitureSpider
from locations.spiders.pick_n_pay import PICK_N_PAY_BRANDS
from locations.spiders.sasol_za import SasolZASpider
from locations.spiders.shell import ShellSpider
from locations.spiders.shoprite_holdings import SHOPRITE_BRANDS
from locations.spiders.spar_bw_mz_na_sz_za import BRANDS as SPAR_BRANDS
from locations.spiders.tops_at_spar import TopsAtSparSpider
from locations.spiders.total_energies import TotalEnergiesSpider
from locations.spiders.woolworths_za import WoolworthsZASpider

DAYS_TERMS = {
    "OpeningHours": DAYS_WEEKDAY,
    "SaturdayHours": "Sa",
    "SundayHours": "Su",
}

LOCATED_IN_MAPPINGS = [
    (["Shoprite"], SHOPRITE_BRANDS["Shoprite"]),
    (["Checkers"], SHOPRITE_BRANDS["Checkers"]),
    (["Usave"], SHOPRITE_BRANDS["Usave"]),
    (["OK Foods"], OK_FOODS_BRANDS["OK FOODS"]),
    (["OK Grocer"], OK_FOODS_BRANDS["OK GROCER"]),
    (["OK Minimark", "OK Mini Mark", "OK Mini"], OK_FOODS_BRANDS["OK MINIMARK"]),
    (["OK Value"], OK_FOODS_BRANDS["OK VALUE"]),
    (["OK Express"], OK_FOODS_BRANDS["OK EXPRESS"]),
    (["OK Furniture"], OkFurnitureSpider.item_attributes),
    (["Superspar"], {**SPAR_BRANDS["SUPERSPAR"][1], "brand": SPAR_BRANDS["SUPERSPAR"][0]}),
    (["KwikSpar"], {**SPAR_BRANDS["KWIKSPAR"][1], "brand": SPAR_BRANDS["KWIKSPAR"][0]}),
    (["Savemor"], SPAR_BRANDS["Savemor"][1]),
    (["Tops"], {**TopsAtSparSpider.item_attributes, "brand": "Tops at Spar"}),
    (["Spar"], {**SPAR_BRANDS["SPAR"][1], "brand": SPAR_BRANDS["SPAR"][0]}),
    (["Pick n Pay"], PICK_N_PAY_BRANDS["PNP"]),
    (["Boxer"], PICK_N_PAY_BRANDS["BOXER"]),
    (["Cambridge Food", "Cambridge"], {"brand": "Cambridge Food", "brand_wikidata": "Q129263104"}),
    (["Food Lover"], FOOD_LOVERS_STORE_TYPES["Store"]),
    (["Alpha Pharm", "Alpha Pharmacy"], AlphaPharmZASpider.item_attributes),
    (["Engen"], EngenSpider.item_attributes),
    (["Caltex"], CaltexSpider.item_attributes),
    (["Shell"], ShellSpider.item_attributes),
    (["BP"], BpSpider.brands["bp"]),
    (["Sasol"], SasolZASpider.item_attributes),
    (["Total"], TotalEnergiesSpider.BRANDS["tot"]),
    (["FreshStop"], FreshstopZASpider.item_attributes),
    (["Woolworths"], WoolworthsZASpider.item_attributes),
    (["Puma"], {"brand": "Puma Energy", "brand_wikidata": "Q7259769"}),
    (["Choppies"], {"brand": "Choppies", "brand_wikidata": "Q5104860"}),
    (["Makro"], dict(zip(["brand", "brand_wikidata"], MetroCashAndCarrySpider.MAKRO))),
    (["Build It"], BuilditSpider.item_attributes),
    (["Game"], GameZASpider.item_attributes),
]


class CapitecBankZASpider(JSONBlobSpider):
    name = "capitec_bank_za"
    item_attributes = {"brand": "Capitec Bank", "brand_wikidata": "Q5035822"}
    locations_key = "Branches"
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 300}
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        # API caps results at the "Take" value; 1000 balances coverage vs duplicate volume
        for lat, lon in country_iseadgg_centroids("ZA", 79):
            yield JsonRequest(
                url="https://www.capitecbank.co.za/api/Branch",
                data={"Latitude": lat, "Longitude": lon, "Take": 1000},
            )

    def pre_process_data(self, feature: dict) -> None:
        # API returns full address in AddressLine1 - rename to Address
        # so DictParser maps it to addr_full instead of street_address
        feature["Address"] = feature.pop("AddressLine1")

    def post_process_item(self, item, response, location):
        if location["IsClosed"]:
            return
        if location["IsAtm"]:
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, location["CashAccepting"], False)
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                location["Name"], LOCATED_IN_MAPPINGS, self
            )
        else:
            item["ref"] = location["Name"].lower().replace(" ", "-")
            apply_category(Categories.BANK, item)

        item["branch"] = item.pop("name")

        oh = OpeningHours()
        for key, days in DAYS_TERMS.items():
            value = location.get(key)
            if not value or "temporarily" in value.lower():
                continue
            if "closed" in value.lower():
                oh.set_closed(days)
            else:
                oh.add_ranges_from_string(value)
        item["opening_hours"] = oh

        yield item
