from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AeropostaleSpider(SitemapSpider, StructuredDataSpider):
    name = "aeropostale"
    item_attributes = {"brand": "Aeropostale", "brand_wikidata": "Q794565"}
    sitemap_urls = ["https://stores.aeropostale.com/sitemap.xml"]
    sitemap_rules = [(r"https://stores.aeropostale.com/.+?/.+/.+?$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
