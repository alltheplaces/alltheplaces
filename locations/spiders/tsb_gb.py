import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TsbGBSpider(SitemapSpider, StructuredDataSpider):
    name = "tsb_gb"
    item_attributes = {"brand": "TSB", "brand_wikidata": "Q7671560"}
    sitemap_urls = ["https://branches.tsb.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/branches\.tsb\.co\.uk\/[-\w]+\/[-\/\w]+\.html$", "parse_sd")]
    wanted_types = ["FinancialService"]
    drop_attributes = {"image"}

    def pre_process_data(self, ld_data: dict, **kwargs):
        rules = []
        for rule in ld_data["openingHours"]:
            if re.match(r"^\w\w (|\d\d:\d\d-\d\d:\d\d|Closed)$", rule):
                rules.append(rule)
            elif m := re.match(r"^(\w\w) (\d\d:\d\d-\d\d:\d\d) (\d\d:\d\d-\d\d:\d\d)$", rule):
                rules.append("{} {}".format(m.group(1), m.group(2)))
                rules.append("{} {}".format(m.group(1), m.group(3)))
            else:
                self.logger.error("Unexpected opening hours format: {}".format(rule))

        ld_data["openingHours"] = rules

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")

        apply_category(Categories.BANK, item)

        yield item

    def extract_amenity_features(self, item, response: Response, ld_item):
        services = [s.get("description") for s in (ld_item.get("amenityFeature") or [])]
        apply_yes_no(Extras.ATM, item, "24/7 cash machine" in services)
        apply_yes_no(Extras.ATM, item, "Cash machine in our branch" in services)
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Accessible" in services)
        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in services)
