from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class SparHRSpider(SitemapSpider, StructuredDataSpider):
    name = "spar_hr"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}

    sitemap_urls = ["https://www.spar.hr/index.sitemap.lokacije-sitemap.xml"]
    sitemap_rules = [("/lokacije/", "parse_sd")]

    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data):
        if "INTERSPAR" in ld_data["name"].upper():
            item["brand"] = "Interspar"
            item["brand_wikidata"] = "Q15820339"
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
    drop_attributes = {"image"}
