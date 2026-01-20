from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class VitusapotekNOSpider(SitemapSpider, StructuredDataSpider):
    name = "vitusapotek_no"
    item_attributes = {"brand": "Vitusapotek", "brand_wikidata": "Q17047215"}
    sitemap_urls = ["https://www.vitusapotek.no/robots.txt"]
    sitemap_rules = [(r"/apotek/NO/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Vitusapotek ")

        item["opening_hours"] = OpeningHours()
        for index, rule in enumerate(ld_data.get("openingHoursSpecification", [])):
            if not isinstance(rule, dict):
                continue
            if rule.get("opens") and rule.get("closes"):
                item["opening_hours"].add_range(DAYS[index], rule["opens"], rule["closes"])

        yield item
