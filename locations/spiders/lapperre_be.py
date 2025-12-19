import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LapperreBESpider(SitemapSpider, StructuredDataSpider):
    name = "lapperre_be"
    item_attributes = {"brand": "Lapperre", "brand_wikidata": "Q126195805"}
    sitemap_urls = ["https://shops.lapperre.be/sitemap.xml"]

    sitemap_rules = [
        (r"https://shops.lapperre.be/nl/.+\.html$", "parse"),
    ]
    wanted_types = ["MedicalBusiness"]

    def parse(self, response, **kwargs):
        response = response.replace(
            body=response.text.replace("health-lifesci.schema.org", "schema.org"),
        )
        yield from self.parse_sd(response)

    def pre_process_data(self, ld_data, **kwargs):
        rules = []
        for rule in ld_data["openingHours"]:
            rule = rule.replace("Gesloten", "Closed")
            rules.append(re.sub(r"(\d\d) (\d\d)", r"\1, \2", rule))
        ld_data["openingHours"] = rules

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
