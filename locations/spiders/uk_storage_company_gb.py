import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class UkStorageCompanyGBSpider(SitemapSpider, StructuredDataSpider):
    name = "uk_storage_company_gb"
    item_attributes = {"brand": "UK Storage Company"}
    sitemap_urls = ["https://www.ukstoragecompany.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/all-locations/[^/]+/[^/]+/$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"opening_hours"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "Coming-Soon" in (item.get("image") or ""):
            return
        item["ref"] = response.url
        item["branch"] = re.sub(r"^UK Storage Company\s*[-–]\s*", "", item.pop("name"))
        if m := re.search(r"destination=(-?\d+\.\d+),(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
