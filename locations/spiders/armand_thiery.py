import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class ArmandThierySpider(CrawlSpider, StructuredDataSpider):
    name = "armand_thiery"
    item_attributes = {"brand": "Armand Thiery", "brand_wikidata": "Q2861975"}
    skip_auto_cc_domain = True

    allowed_domains = ["www.armandthiery.fr"]
    start_urls = ["https://www.armandthiery.fr/fr/magasins/recherche.cfm"]
    rules = [Rule(LinkExtractor(allow=["/fr/magasins/"]), callback="parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["rules"] = ld_data.pop("openingHours", [])

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        item["opening_hours"] = self.parse_hours(ld_data.get("rules", []))
        apply_category(Categories.SHOP_CLOTHES, item)
        store_type, item["branch"] = item.pop("name").split(" - ", 1)
        clothes = set()
        if "FEMME" in store_type or "TOSCA" in store_type:
            clothes.add("women")
        if "HOMME" in store_type:
            clothes.add("men")
        item["extras"]["clothes"] = ";".join(sorted(clothes))
        yield item

    @staticmethod
    def parse_hours(rules: list[str]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day, _, times = rule.partition(" : ")
            if not (day := sanitise_day(day, DAYS_FR)):
                continue
            if times.strip() == "-":
                oh.set_closed(day)
                continue
            for start_time, end_time in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", times):
                oh.add_range(day, start_time, end_time)
        return oh
