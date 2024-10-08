from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider

SUPA_QUICK_BRANDS = ["Supa Quick Express", "Supa Quick Tyre Experts"]


class SupaQuickSpider(SitemapSpider, StructuredDataSpider):
    name = "supa_quick"
    item_attributes = {"brand": "Supa Quick", "brand_wikidata": "Q121133344"}
    sitemap_urls = ["https://www.supaquick.com/robots.txt"]
    sitemap_rules = [("/tyre-fitment-centres/", "parse_sd")]
    wanted_types = ["TireShop"]
    download_timeout = 30  # The default timeout led to a a lot of requests timing out

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["facebook"] == "https://www.facebook.com/supaquick":
            item.pop("facebook")
        for brand in SUPA_QUICK_BRANDS:
            if "name" in item and brand in item["name"]:
                item["brand"] = brand
                item["branch"] = item.pop("name").replace(brand, "").strip()
        item["opening_hours"] = OpeningHours()
        for row in response.xpath('.//div[contains(text(), "REGULAR HOURS")]/.././/table/tr'):
            item["opening_hours"].add_ranges_from_string(row.xpath("string(.)").get())
        yield item
