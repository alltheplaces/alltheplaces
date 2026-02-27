from scrapy.spiders import SitemapSpider

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.spiders.caseys_general_store import CaseysGeneralStoreSpider
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.costco_ca_gb_us import CostcoCAGBUSSpider
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.food_lion_us import FoodLionUSSpider
from locations.spiders.giant_food_stores import GiantFoodStoresSpider
from locations.spiders.giant_food_us import GiantFoodUSSpider
from locations.spiders.kroger_us import BRANDS as KROGER_BRANDS
from locations.spiders.safeway import SafewaySpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.speedway_us import SpeedwayUSSpider
from locations.spiders.stop_and_shop_us import StopAndShopUSSpider
from locations.spiders.target_us import TargetUSSpider
from locations.spiders.tim_hortons import TimHortonsSpider
from locations.spiders.walgreens import WalgreensSpider
from locations.spiders.walmart_us import WalmartUSSpider
from locations.spiders.wegmans_us import WegmansUSSpider
from locations.structured_data_spider import StructuredDataSpider


class MtBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "mt_bank_us"
    item_attributes = {"brand": "M&T Bank", "brand_wikidata": "Q3272257"}
    sitemap_urls = ["https://locations.mtb.com/robots.txt"]
    sitemap_rules = [(r"\.html$", "parse_sd")]
    wanted_types = ["FinancialService"]
    drop_attributes = {"image"}

    LOCATED_IN_MAPPINGS = [
        (["STOP & SHOP", "STOP AND SHOP"], StopAndShopUSSpider.item_attributes),
        (["7ELEVEN", "7-ELEVEN"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
        (["WALGREENS"], WalgreensSpider.WALGREENS),
        (["DUANE READE"], WalgreensSpider.DUANE_READE),
        (["CVS"], CVS_BRANDS["CVS Pharmacy"]),
        (["CIRCLE K", "CIRCLEK"], CircleKSpider.CIRCLE_K),
        (["TARGET"], TargetUSSpider.item_attributes),
        (["CASEY"], CaseysGeneralStoreSpider.item_attributes),
        (["COSTCO"], CostcoCAGBUSSpider.item_attributes),
        (["WALMART", "WAL-MART"], WalmartUSSpider.item_attributes),
        (["KROGER"], KROGER_BRANDS["https://www.kroger.com/"]),
        (["WEGMANS"], WegmansUSSpider.item_attributes),
        (["SAFEWAY"], SafewaySpider.item_attributes),
        (["GIANT FOOD STORES"], GiantFoodStoresSpider.item_attributes),
        (["GIANT FOOD"], GiantFoodUSSpider.item_attributes),
        (["HARRIS TEETER", "HARRISTEETER"], KROGER_BRANDS["https://www.harristeeter.com/"]),
        (["FOOD LION"], FoodLionUSSpider.item_attributes),
        (["DELTA SONIC"], {"brand": "Delta Sonic", "brand_wikidata": "Q126914775"}),
        (["EXXON"], ExxonMobilSpider.brands["Exxon"]),
        (["QUICK CHEK"], {"brand": "QuickChek", "brand_wikidata": "Q7271689"}),
        (["SPEEDWAY"], SpeedwayUSSpider.item_attributes),
        (["TIM HORTONS"], TimHortonsSpider.item_attributes),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        cat = response.xpath('//span[@class="Hero-locationType"]/text()').get()
        if cat == "ATM Only":
            apply_category(Categories.ATM, item)
            name = item.pop("name")
            item["located_in"], item["located_in_wikidata"] = extract_located_in(name, self.LOCATED_IN_MAPPINGS, self)
        elif cat in ["Branch & ATM", "Branch"]:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, cat == "Branch & ATM")

            if not item.get("name") or not item["name"].startswith("M&T Bank in "):
                # Duplicates, eg:
                # https://locations.mtb.com/ma/agawam/bank-branches-and-atms-agawam-ma-8422.html
                # https://locations.mtb.com/ma/agawam/bank-branches-and-atms-agawam-ma-sa7000.html
                return
            item["branch"] = item.pop("name").removeprefix("M&T Bank in ")

        yield item
