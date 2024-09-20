import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
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
                item["extras"]["opening_hours:pharmacy"] = LinkedDataParser.parse_opening_hours(
                    department
                ).as_opening_hours()
                break

        # If there is no retail opening_hours, use the pharmacy hours
        # If there is a default retail opening_hours, add that to extras
        if not item.get("opening_hours") and item["extras"].get("opening_hours:pharmacy"):
            item["opening_hours"] = item["extras"]["opening_hours:pharmacy"]
        else:
            item["extras"]["opening_hours:retail"] = item["opening_hours"].as_opening_hours()

        apply_category(Categories.PHARMACY, item)
        yield item
