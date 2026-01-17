from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.bp import BpSpider
from locations.spiders.caltex import CaltexSpider
from locations.spiders.engen import EngenSpider
from locations.spiders.ok_foods import OK_FOODS_BRANDS
from locations.spiders.sasol_za import SasolZASpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.shell import ShellSpider
from locations.spiders.shoprite_holdings import SHOPRITE_BRANDS
from locations.spiders.spar_bw_mz_na_sz_za import BRANDS as SPAR_BRANDS
from locations.spiders.total_energies import TotalEnergiesSpider
from locations.spiders.tymebank_za import PICK_N_PAY_BRANDS
from locations.spiders.usave_gb import UsaveGBSpider
from locations.spiders.woolworths_za import WoolworthsZASpider


class AbsaZASpider(JSONBlobSpider):
    name = "absa_za"
    item_attributes = {"brand": "ABSA", "brand_wikidata": "Q58641733"}
    start_urls = ["https://www.absa.co.za/etc/barclays/contact-info/south-africa/_jcr_content/locations.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    LOCATED_IN_MAPPINGS = [
        (["ENGEN"], EngenSpider.item_attributes),
        (["SHELL"], ShellSpider.item_attributes),
        (["CALTEX"], CaltexSpider.item_attributes),
        (["BP"], BpSpider.brands["bp"]),
        (["TOTAL"], TotalEnergiesSpider.BRANDS["tot"]),
        (["SPAR"], SPAR_BRANDS["SPAR"][1]),
        (["SUPERSPAR"], SPAR_BRANDS["SUPERSPAR"][1]),
        (["KWIKSPAR"], SPAR_BRANDS["KWIKSPAR"][1]),
        (["PNP"], PICK_N_PAY_BRANDS["PNP"]),
        (["BOXER"], PICK_N_PAY_BRANDS["BOXER"]),
        (["SHOPRITE"], SHOPRITE_BRANDS["Shoprite"]),
        (["CHECKERS"], SHOPRITE_BRANDS["Checkers"]),
        (["WOOLWORTHS"], WoolworthsZASpider.item_attributes),
        (["7 ELEVEN"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
        (["SASOL"], SasolZASpider.item_attributes),
        (["BUILDERS"], {"brand": "Builders", "brand_wikidata": "Q133971381"}),
        (["U SAVE"], UsaveGBSpider.item_attributes),
        (["OK VALUE"], OK_FOODS_BRANDS["OK VALUE"]),
        (["OK GROCER"], OK_FOODS_BRANDS["OK GROCER"]),
        (["OK MINI", "OK MINIMARKET"], OK_FOODS_BRANDS["OK MINIMARK"]),
        (["GAME"], {"brand": "Game", "brand_wikidata": "Q126811048"}),
    ]

    def post_process_item(self, item, response, location):
        if location["type"] == "branch":
            apply_category(Categories.BANK, item)
        elif location["type"] == "atm":
            apply_category(Categories.ATM, item)
            # Extract retail brand from name field for ATMs (before it's moved to branch)
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                item.get("name", ""), self.LOCATED_IN_MAPPINGS, self
            )
        else:
            # there are a number of "dealer" types, ignore
            return

        item["addr_full"] = clean_address(item["addr_full"])
        try:
            int(item["addr_full"].split(" ")[0])
            item["housenumber"] = item["addr_full"].split(" ")[0]
            item["street"] = item["addr_full"].split(",")[0].replace(item["housenumber"], "").strip()
        except ValueError:
            pass

        item["branch"] = item.pop("name")
        if "weekdayHours" in location and "weekendHours" in location:
            oh = OpeningHours()
            for times in location.get("weekdayHours").split(";"):
                oh.add_ranges_from_string("Mo-Fr " + times)
            for day_times in location.get("weekendHours").split(","):
                day, times = day_times.split(": ")
                if "closed" in times.lower():
                    oh.set_closed(day)
                else:
                    oh.add_ranges_from_string(day_times)
            item["opening_hours"] = oh.as_opening_hours()
        yield item
