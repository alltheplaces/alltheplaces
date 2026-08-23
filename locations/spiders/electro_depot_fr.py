from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class ElectroDepotFRSpider(SitemapSpider, StructuredDataSpider):
    name = "electro_depot_fr"
    item_attributes = {
        "brand": "Électro Dépôt",
        "brand_wikidata": "Q2388060",
        "extras": Categories.SHOP_ELECTRONICS.value,
    }
    sitemap_urls = ["https://magasins.electrodepot.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"https://magasins\.electrodepot\.fr/fr/france-FR/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness", "ElectronicsStore"]
    drop_attributes = {"image", "twitter"}
