from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LaFoirfouilleFRSpider(SitemapSpider, StructuredDataSpider):
    name = "la_foirfouille_fr"
    item_attributes = {"brand": "La Foir'Fouille", "brand_wikidata": "Q3209040"}
    sitemap_urls = ["https://www.lafoirfouille.fr/magasins.xml"]
    sitemap_rules = [(r"/la-?foir-?fouille", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
