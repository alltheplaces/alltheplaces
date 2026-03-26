import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


def apply_category_from_ld(item, ld_data: {}):
    if ld_data["@type"] == "Pharmacy":
        apply_category(Categories.PHARMACY, item)
    elif ld_data["@type"] == "GasStation":
        apply_category(Categories.FUEL_STATION, item)
    elif ld_data["@type"] == "CafeOrCoffeeShop":
        apply_category(Categories.CAFE, item)


def set_located_in(brand: {}, item):
    if brand.get("located_in") or brand.get("located_in_wikidata"):
        item["located_in"] = brand.get("located_in")
        item["located_in_wikidata"] = brand.get("located_in_wikidata")
    elif brand.get("brand") or brand.get("brand_wikidata"):
        item["located_in"] = brand.get("brand")
        item["located_in_wikidata"] = brand.get("brand_wikidata")


class TescoGBSpider(SitemapSpider, StructuredDataSpider):
    name = "tesco_gb"
    TESCO = {"brand": "Tesco", "brand_wikidata": "Q487494"}
    TESCO_EXTRA = {"brand": "Tesco Extra", "brand_wikidata": "Q25172225"}
    TESCO_EXPRESS = {"brand": "Tesco Express", "brand_wikidata": "Q98456772"}
    # Tesco Metro is only in Ireland
    TESCO_METRO = {"brand": "Tesco Metro", "brand_wikidata": "Q57551648"}
    item_attributes = TESCO
    sitemap_urls = ["https://www.tesco.com/store-locator/sitemap.xml"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}
    requires_proxy = True
    strip_names = [
        "Tesco Café",
        "Tesco Petrol Filling Station",
        "Tesco Pharmacy",
        "Extra",
        "Superstore",
        "Express",
        "Esso",
        "Metro",
    ]
    drop_attributes = {"email", "image"}

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        if "openingHours" in ld_data and isinstance(ld_data["openingHours"], list):
            # Clean up some non-standard coding of being open all hours.
            ld_data["openingHours"] = [
                hours.replace("All Day", "00:00-23:59") if isinstance(hours, str) else hours
                for hours in ld_data["openingHours"]
            ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category_from_ld(item, ld_data)
        if ld_data["@type"] in ["Pharmacy", "GasStation", "CafeOrCoffeeShop"]:
            self.set_located_in(item)
        elif ld_data["@type"] == "GroceryStore":
            store_details = json.loads(response.xpath('//script[@id="storeData"]/text()').get())
            item["ref"] = store_details["store"]
            if store_details["storeformat"] == "Express":
                apply_category(Categories.SHOP_CONVENIENCE, item)
                item.update(self.TESCO_EXPRESS)
            elif store_details["storeformat"] == "Superstore":
                apply_category(Categories.SHOP_SUPERMARKET, item)
                item.update(self.TESCO)
            elif store_details["storeformat"] == "Extra":
                apply_category(Categories.SHOP_SUPERMARKET, item)
                item.update(self.TESCO_EXTRA)
            elif store_details["storeformat"] == "Metro":
                apply_category(Categories.SHOP_SUPERMARKET, item)
                item.update(self.TESCO_METRO)
        else:
            # This is skipping ClothingStore (obvious) and LocalBusiness (Travel Money) types
            self.crawler.stats.inc_value(f'atp/ld_type/{ld_data["@type"]}/ignore')
            return

        if branch := item.pop("name"):
            if self.name == "tesco_ie":
                # The Irish site has tagged on extra compared to GB site, see tesco_ie.py
                branch = branch.split("  ")[0]
            for suffix in self.strip_names:
                branch = branch.strip().removesuffix(suffix)
            item["branch"] = branch.strip()

        yield item

    def set_located_in(self, item):
        if "Express" in item["name"]:
            set_located_in(self.TESCO_EXPRESS, item)
        elif "Superstore" in item["name"]:
            set_located_in(self.TESCO, item)
        elif "Extra" in item["name"]:
            set_located_in(self.TESCO_EXTRA, item)
