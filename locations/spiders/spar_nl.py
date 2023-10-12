from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SparNLSpider(SitemapSpider, StructuredDataSpider):
    name = "spar_nl"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}
    sitemap_urls = ["https://www.spar.nl/sitemap/stores.xml/"]
    sitemap_rules = [(r"/winkels/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "express" in item.get("name", ""):
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
