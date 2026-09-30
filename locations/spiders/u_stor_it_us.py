from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class UStorItUSSpider(SitemapSpider, StructuredDataSpider):
    name = "u_stor_it_us"
    item_attributes = {"brand": "U-Stor-It", "brand_wikidata": "Q116225856", "name": "U-Stor-It"}
    sitemap_urls = ["https://www.ustorit.com/sitemap.xml"]
    sitemap_rules = [(r"/storage/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        item.pop("name", None)
        item["country"] = "US"
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
