from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class AuVideGrenierFRSpider(SitemapSpider, StructuredDataSpider):
    name = "au_vide_grenier_fr"
    item_attributes = {
        "brand": "Au Vide Grenier",
        "brand_wikidata": "Q141175815",
        "extras": Categories.SHOP_SECOND_HAND.value,
    }
    sitemap_urls = ["https://auvidegrenier.fr/sitemap/shops.xml"]
    sitemap_rules = [(r"https:\/\/auvidegrenier\.fr\/magasins\/", "parse_sd")]
    drop_attributes = {"image"}
