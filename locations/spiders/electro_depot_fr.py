from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ElectroDepotFRSpider(SitemapSpider, StructuredDataSpider):
    name = "electro_depot_fr"
    item_attributes = {
        "brand": "Électro Dépôt",
        "brand_wikidata": "Q2388060",
    }
    sitemap_urls = ["https://magasins.electrodepot.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"https://magasins\.electrodepot\.fr/fr/france-FR/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness", "ElectronicsStore"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
