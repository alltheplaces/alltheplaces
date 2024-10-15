from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PetitBateauSpider(SitemapSpider, StructuredDataSpider):
    name = "petit_bateau"
    item_attributes = {"brand": "Petit Bateau", "brand_wikidata": "Q3377090"}
    sitemap_urls = ["https://stores.petit-bateau.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/stores\.petit-bateau\.com\/[a-z\-]{3,}\/.+", "parse_sd")]
    wanted_types = ["ClothingStore"]
    drop_attributes = {"image"}
