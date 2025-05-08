import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RousesUSSpider(SitemapSpider, StructuredDataSpider):
    name = "rouses_us"
    item_attributes = {"brand": "Rouses", "brand_wikidata": "Q7371327"}
    allowed_domains = ["www.rouses.com"]
    sitemap_urls = ["https://www.rouses.com/locations-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.rouses\.com\/locations\/rouses(?:-market|-store)-(\d+)\/$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item.pop("twitter", None)
        if m := re.match(
            r"(\d{1,2}(?::\d{1,2})?(?:am|pm))\s*-\s*(\d{1,2}(?::\d{1,2})?(?:am|pm))\s*<\/br>\s*Daily",
            ld_data.get("openingHours", ""),
            flags=re.IGNORECASE,
        ):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string("Mo-Su: {}-{}".format(m.group(1), m.group(2)))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
