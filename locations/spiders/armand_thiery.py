from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR
from locations.structured_data_spider import StructuredDataSpider


class ArmandThierySpider(CrawlSpider, StructuredDataSpider):
    name = "armand_thiery"
    item_attributes = {"brand": "Armand Thiery", "brand_wikidata": "Q2861975"}
    skip_auto_cc_domain = True

    allowed_domains = ["www.armandthiery.fr"]
    start_urls = ["https://www.armandthiery.fr/fr/magasins/recherche.cfm"]
    rules = [Rule(LinkExtractor(allow=["/fr/magasins/"]), callback="parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        formatted_rules = []
        for rule in ld_data.get("openingHours", []):
            if rule.endswith(" : -"):  # Closed, currently errors in add_range
                continue
            for fr, en in DAYS_FR.items():
                rule = rule.replace(fr, en)  # Translate
            rule = rule.replace(" : ", " ")  # Fix seperator
            formatted_rules.append(rule)
        ld_data["openingHours"] = formatted_rules

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        apply_category(Categories.SHOP_CLOTHES, item)
        store_type, item["branch"] = item.pop("name").split(" - ", 1)
        clothes = set()
        if "FEMME" in store_type or "TOSCA" in store_type:
            clothes.add("women")
        if "HOMME" in store_type:
            clothes.add("men")
        item["extras"]["clothes"] = ";".join(sorted(clothes))
        yield item
