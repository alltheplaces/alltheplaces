import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RiteAidUSSpider(SitemapSpider, StructuredDataSpider):
    name = "rite_aid_us"
    item_attributes = {"brand": "Rite Aid", "brand_wikidata": "Q3433273"}
    allowed_domains = ["locations2.riteaid.com.yext-cdn.com"]
    sitemap_urls = ("https://locations2.riteaid.com.yext-cdn.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://locations2.riteaid.com.yext-cdn.com/[^/]+/[^/]+/[^/]+.html$", "parse_sd"),
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    wanted_types = ["Store"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "www.riteaid.com/locations/" in entry.get("loc"):
                entry["loc"] = entry["loc"].replace(
                    "www.riteaid.com/locations/", "locations2.riteaid.com.yext-cdn.com/"
                )
                yield entry

    def post_process_item(self, item, response, ld_data):
        if m := re.match(r"^Rite Aid #(\d+)\s", item["name"]):
            item["ref"] = m.group(1)
        item["website"] = item["website"].replace("www.riteaid.com/locations/", "locations2.riteaid.com.yext-cdn.com/")
        item.pop("image")
        item.pop("twitter")
        yield item
