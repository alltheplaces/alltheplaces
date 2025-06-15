from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AdlerModemarkteSpider(SitemapSpider, StructuredDataSpider):
    name = "adler_modemarkte"
    item_attributes = {"brand": "Adler", "brand_wikidata": "Q358196"}
    sitemap_urls = ["https://adler.de/wp-sitemap.xml"]
    sitemap_follow = ["place"]
    sitemap_rules = [(r"/standorte/[^/]+/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item.pop("email")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
