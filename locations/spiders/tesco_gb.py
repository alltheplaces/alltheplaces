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
    item_attributes = TESCO
    sitemap_urls = ["https://www.tesco.com/store-locator/sitemap.xml"]
    sitemap_rules = [
        (r"/pharmacy$", "parse_sd"),
        (r"/petrol-filling-station$", "parse_sd"),
        (r"/cafe$", "parse_sd"),
        (r"/store-locator/[-\w]+/[-\w]+$", "parse_sd"),
    ]
    wanted_types = ["Pharmacy", "GasStation", "CafeOrCoffeeShop", "GroceryStore"]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True
    strip_names = [
        "Tesco Café",
        "Tesco Petrol Filling Station",
        "Tesco Pharmacy",
        "Extra",
        "Superstore",
        "Express",
        "Esso",
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

        item["image"] = None

        branch = item.pop("name")
        for suffix in self.strip_names:
            branch = branch.removesuffix(suffix).removesuffix(" ")
        item["branch"] = branch

        yield item

    def set_located_in(self, item):
        if "Express" in item["name"]:
            set_located_in(self.TESCO_EXPRESS, item)
        elif "Superstore" in item["name"]:
            set_located_in(self.TESCO, item)
        elif "Extra" in item["name"]:
            set_located_in(self.TESCO_EXTRA, item)
