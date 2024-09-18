from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FotoprixESSpider(SitemapSpider, StructuredDataSpider):
    name = "fotoprix_es"
    item_attributes = {
        # Uncomment and populate if known
        "brand": "Fotoprix",
        "brand_wikidata": "Q99196842",
        # "operator": "None",
        # "operator_wikidata": "None",
        # "extras": Categories.SHOP_XYZ.value
    }
    sitemap_urls = ["https://www.fotoprix.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.fotoprix.com/tiendas/[\w-]+/[\w-]+", "parse"),
    ]
    # wanted_types = ["GroceryStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        yield item
