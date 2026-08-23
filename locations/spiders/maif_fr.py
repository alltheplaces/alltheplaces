from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MaifFRSpider(SitemapSpider, StructuredDataSpider):
    name = "maif_fr"
    item_attributes = {"brand": "Maif", "brand_wikidata": "Q3331029"}
    sitemap_urls = ["https://agence.maif.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"/details$", "parse_sd")]
