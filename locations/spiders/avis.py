from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class AvisSpider(SitemapSpider, StructuredDataSpider):
    name = "avis"
    item_attributes = {"brand": "Avis", "brand_wikidata": "Q791136"}
    sitemap_urls = ["https://www.avis.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.avis.com/en/locations/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["AutoRental"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("name"):
            item["branch"] = item.pop("name").removeprefix("Avis ")
        oh = OpeningHours()
        for day_time in ld_data["openingHours"]:
            if "24 hrs" in day_time:
                item["opening_hours"] = "24/7"
            else:
                oh.add_ranges_from_string(day_time)
                item["opening_hours"] = oh
        apply_category(Categories.CAR_RENTAL, item)

        yield item
