import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.spiders.costcutter_gb import CostcutterGBSpider
from locations.spiders.james_retail_gb import JamesRetailGBSpider
from locations.spiders.the_food_warehouse_gb import TheFoodWarehouseGBSpider
from locations.structured_data_spider import StructuredDataSpider


class BargainBoozeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bargain_booze_gb"
    item_attributes = {"brand": "Bargain Booze", "brand_wikidata": "Q16971315", "extras": Categories.SHOP_ALCOHOL.value}
    allowed_domains = ["branches.bargainbooze.co.uk"]
    sitemap_urls = ["https://branches.bargainbooze.co.uk/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/branches\.bargainbooze\.co\.uk\/[\w\-]+\/[\w\-]+\.html$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        if "CLOSED" in item["name"].upper() or "COMING SOON" in item["name"].upper():
            return
        item["city"] = item.pop("state", None)
        item["name"] = re.sub(
            r"\s*(?:Bargain Booze(?: Plus)?|-?\s*Under New Management|-?\s*Sole Trader|-?\s*Now Open|\.{2,})\s*",
            " ",
            item["name"],
            flags=re.IGNORECASE,
        ).strip()
        if "SELECT CONVENIENCE" in item["name"].upper() or "SELECT CONVENINECE" in item["name"].upper():
            item["brand"] = "Bargain Booze Select Convenience"
            item["brand_wikidata"] = "Q124473514"
            item["name"] = re.sub(
                r"\s*(?:Select Convenience|Select Conveninece)\s*", " ", item["name"], flags=re.IGNORECASE
            ).strip()
        elif "SUPERNEWS" in item["name"].upper():
            item["located_in"] = JamesRetailGBSpider.brands["SUPERNEWS"]["brand"]
            item["located_in_wikidata"] = JamesRetailGBSpider.brands["SUPERNEWS"]["brand_wikidata"]
            item["name"] = re.sub(r"\s*(?:Supernews)\s*", " ", item["name"], flags=re.IGNORECASE).strip()
        elif (
            "INSIDE FOOD WAREHOUSE" in item["name"].upper()
            or "THE FOOD WAREHOUSE" in item["name"].upper()
            or "FOOD WAREHOUSE" in item["name"].upper()
        ):
            item["located_in"] = TheFoodWarehouseGBSpider.item_attributes["brand"]
            item["located_in_wikidata"] = TheFoodWarehouseGBSpider.item_attributes["brand_wikidata"]
            item["name"] = re.sub(
                r"\s*(?:Inside Food Warehouse|The Food Warehouse|Food Warehouse)\s*",
                " ",
                item["name"],
                flags=re.IGNORECASE,
            ).strip()
        elif (
            "INSIDE A COSTCUTTER" in item["name"].upper()
            or "INSIDE COSTCUTTER" in item["name"].upper()
            or "COSTCUTTER" in item["name"].upper()
        ):
            item["located_in"] = CostcutterGBSpider.item_attributes["brand"]
            item["located_in_wikidata"] = CostcutterGBSpider.item_attributes["brand_wikidata"]
            item["name"] = re.sub(
                r"\s*(?:Inside a Costcutter|Inside Costcutter|Costcutter)\s*", " ", item["name"], flags=re.IGNORECASE
            ).strip()
        item.pop("facebook")
        item.pop("twitter")
        item.pop("image")
        yield item
