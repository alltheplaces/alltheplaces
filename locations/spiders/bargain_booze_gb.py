import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.spiders.costcutter_gb import CostcutterGBSpider
from locations.spiders.james_retail_gb import JamesRetailGBSpider
from locations.spiders.the_food_warehouse_gb import TheFoodWarehouseGBSpider
from locations.structured_data_spider import StructuredDataSpider


class BargainBoozeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bargain_booze_gb"
    item_attributes = {"brand": "Bargain Booze", "brand_wikidata": "Q16971315"}
    allowed_domains = ["branches.bargainbooze.co.uk"]
    sitemap_urls = ["https://branches.bargainbooze.co.uk/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/branches\.bargainbooze\.co\.uk\/[\w\-]+\/[\w\-]+\.html$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        if "CLOSED" in item["name"].upper() or "COMING SOON" in item["name"].upper():
            return
        name = item["name"]
        item["city"] = item.pop("state", None)
        item["branch"] = re.sub(
            r"\s*(?:Bargain Booze(?: Plus)?|-?\s*Under New Management|-?\s*Sole Trader|-?\s*Now Open|\.{2,})\s*",
            " ",
            name,
            flags=re.IGNORECASE,
        ).strip()
        item["name"] = "Bargain Booze"
        if "SELECT CONVENIENCE" in name.upper() or "SELECT CONVENINECE" in name.upper():
            item["brand"] = "Bargain Booze Select Convenience"
            item["brand_wikidata"] = "Q124473514"
            item["branch"] = re.sub(
                r"\s*(?:Select Convenience|Select Conveninece|Bargain Booze)\s*", " ", name, flags=re.IGNORECASE
            ).strip()
            item["name"] = "Bargain Booze Select Convenience"
        elif "SUPERNEWS" in name.upper():
            item["located_in"] = JamesRetailGBSpider.brands["SUPERNEWS"]["brand"]
            item["located_in_wikidata"] = JamesRetailGBSpider.brands["SUPERNEWS"]["brand_wikidata"]
            item["branch"] = re.sub(r"\s*(?:Supernews)\s*", " ", name, flags=re.IGNORECASE).strip()
            item["name"] = "Supernews"
        elif (
            "INSIDE FOOD WAREHOUSE" in name.upper()
            or "THE FOOD WAREHOUSE" in name.upper()
            or "FOOD WAREHOUSE" in name.upper()
        ):
            item["located_in"] = TheFoodWarehouseGBSpider.item_attributes["brand"]
            item["located_in_wikidata"] = TheFoodWarehouseGBSpider.item_attributes["brand_wikidata"]
            item["branch"] = re.sub(
                r"\s*(?:Inside Food Warehouse|The Food Warehouse|Food Warehouse)\s*",
                " ",
                name,
                flags=re.IGNORECASE,
            ).strip()
            item["name"] = "Bargain Booze in The Food Warehouse"
        elif (
            "INSIDE A COSTCUTTER" in name.upper() or "INSIDE COSTCUTTER" in name.upper() or "COSTCUTTER" in name.upper()
        ):
            item["located_in"] = CostcutterGBSpider.item_attributes["brand"]
            item["located_in_wikidata"] = CostcutterGBSpider.item_attributes["brand_wikidata"]
            item["branch"] = re.sub(
                r"\s*(?:Inside a Costcutter|Inside Costcutter|Costcutter|Featuring Bargain Booze)\s*",
                " ",
                name,
                flags=re.IGNORECASE,
            ).strip()
            item["name"] = "Bargain Booze in Costcutter"
        item.pop("facebook")
        item.pop("twitter")
        item.pop("image")
        apply_category(Categories.SHOP_ALCOHOL, item)
        yield item
