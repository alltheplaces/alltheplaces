from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AuVieuxCampeurSpider(SitemapSpider, StructuredDataSpider):
    name = "au_vieux_campeur"
    item_attributes = {
        "brand": "Au vieux campeur",
        "brand_wikidata": "Q2409646",
    }
    allowed_domains = ["boutiques.auvieuxcampeur.fr"]
    sitemap_urls = ["https://boutiques.auvieuxcampeur.fr/sitemap.xml"]
    sitemap_rules = [
        (
            r"^https?://boutiques.auvieuxcampeur.fr(?:/[^/]+)*/[^/]+-\d{2,3}/?$",
            "parse_sd",
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.SHOP_OUTDOOR, item)
        yield item
