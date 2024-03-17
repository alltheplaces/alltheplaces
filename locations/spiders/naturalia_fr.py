from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NaturaliaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "naturalia_fr"
    item_attributes = {"brand": "Naturalia", "brand_wikidata": "Q3337081"}
    sitemap_urls = ["https://magasins.naturalia.fr/sitemap.xml"]
    sitemap_rules = [(r"https://magasins.naturalia.fr/naturalia/fr/store/.*", "parse_sd")]
