import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class RiteAidUSSpider(SitemapSpider, StructuredDataSpider):
    name = "rite_aid_us"
    item_attributes = {"brand": "Rite Aid", "brand_wikidata": "Q3433273"}
    sitemap_urls = ["https://www.riteaid.com/robots.txt"]
    sitemap_follow = ["locations"]
    sitemap_rules = [(r"^https://www.riteaid.com/locations/[^/]+/[^/]+/[^/]+.html$", "parse_sd")]
    wanted_types = ["Store"]

    def post_process_item(self, item, response, ld_data):
        if m := re.match(r"^Rite Aid #(\d+)\s", item.pop("name")):
            item["ref"] = m.group(1)

        item.pop("image")
        item.pop("twitter")

        for department in ld_data.get("department", []):
            if department.get("@type") == "Pharmacy":
                pharmacy = item.deepcopy()
                pharmacy["ref"] = "{}-pharmacy".format(item["ref"])
                pharmacy["phone"] = department["telephone"]
                pharmacy["opening_hours"] = OpeningHours()
                pharmacy["opening_hours"].from_linked_data(department)
                apply_category(Categories.PHARMACY, pharmacy)
                yield pharmacy
                break

        apply_category(Categories.SHOP_CHEMIST, item)
        yield item
