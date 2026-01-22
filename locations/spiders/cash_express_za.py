from locations.brand_utils import extract_located_in
from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.bp import BpSpider
from locations.spiders.buildit import BuilditSpider
from locations.spiders.caltex import CaltexSpider
from locations.spiders.engen import EngenSpider
from locations.spiders.ok_foods import OK_FOODS_BRANDS
from locations.spiders.sasol_za import SasolZASpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.shell import ShellSpider
from locations.spiders.shoprite_holdings import SHOPRITE_BRANDS
from locations.spiders.spar_bw_mz_na_sz_za import BRANDS as SPAR_BRANDS
from locations.spiders.tops_at_spar import TopsAtSparSpider
from locations.spiders.total_energies import TotalEnergiesSpider
from locations.spiders.tymebank_za import PICK_N_PAY_BRANDS
from locations.spiders.usave_gb import UsaveGBSpider


class CashExpressZASpider(JSONBlobSpider):
    name = "cash_express_za"
    item_attributes = {
        "brand": "Cash Express",
        "brand_wikidata": "Q130262361",
        "extras": Categories.ATM.value,
    }
    start_urls = ["https://www.bidvestbank.co.za/assets/mock/cash-express-branded-atms.json"]

    LOCATED_IN_MAPPINGS = [
        (["ENGEN"], EngenSpider.item_attributes),
        (["CALTEX"], CaltexSpider.item_attributes),
        (["TOTAL"], TotalEnergiesSpider.BRANDS["tot"]),
        (["BP"], BpSpider.brands["bp"]),
        (["SASOL"], SasolZASpider.item_attributes),
        (["SHELL"], ShellSpider.item_attributes),
        (
            ["SUPERSPAR", "SPARGS"],
            {"brand": SPAR_BRANDS["SUPERSPAR"][0], "brand_wikidata": SPAR_BRANDS["SUPERSPAR"][1]["brand_wikidata"]},
        ),
        (
            ["KWIKSPAR"],
            {"brand": SPAR_BRANDS["KWIKSPAR"][0], "brand_wikidata": SPAR_BRANDS["KWIKSPAR"][1]["brand_wikidata"]},
        ),
        (
            ["SAVEMOR", "SAVEMORE", "SAVE MORE"],
            {"brand": SPAR_BRANDS["Savemor"][0], "brand_wikidata": SPAR_BRANDS["Savemor"][1]["brand_wikidata"]},
        ),
        (["SPAR"], SPAR_BRANDS["SPAR"][1]),
        (["SHOPRITE"], SHOPRITE_BRANDS["Shoprite"]),
        (["CHECKERS"], SHOPRITE_BRANDS["Checkers"]),
        (["7-11"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
        (["BUILD IT", "BUILD-IT", "BUILDIT"], BuilditSpider.item_attributes),
        (["PICK N PAY", "PNP"], PICK_N_PAY_BRANDS["PNP"]),
        (["OK FOODS", "OKFOODS"], OK_FOODS_BRANDS["OK FOODS"]),
        (["OK GROCER"], OK_FOODS_BRANDS["OK GROCER"]),
        (["OK VALUE"], OK_FOODS_BRANDS["OK VALUE"]),
        (["OK LIQUOR", "OK LIQ"], OK_FOODS_BRANDS["OK LIQUOR"]),
        (["OK EXPRESS", "OKEXPRESS"], OK_FOODS_BRANDS["OK EXPRESS"]),
        (["OK MINI", "OK MINIMARK", "OK MINIMKT"], OK_FOODS_BRANDS["OK MINIMARK"]),
        (["MAKRO"], {"brand": "Makro", "brand_wikidata": "Q704606"}),
        (["TOPS"], TopsAtSparSpider.item_attributes),
        (["U-SAVE", "USAVE"], UsaveGBSpider.item_attributes),
    ]

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("Device id")
        location["branch"] = location.pop("Site Name")
        location["Latitude"] = location["Latitude"].replace(",", ".")
        location["Longitude"] = location["Longitude"].replace(",", ".")
        location["street_address"] = location.pop("Street Address")

    def post_process_item(self, item, response, location):
        item["located_in"], item["located_in_wikidata"] = extract_located_in(
            location.get("branch", ""), self.LOCATED_IN_MAPPINGS, self
        )
        yield item
