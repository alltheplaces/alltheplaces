from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MaisonDeLaLiterieFRSpider(SitemapSpider, StructuredDataSpider):
    name = "maison_de_la_literie_fr"
    item_attributes = {"brand": "Maison de la Literie", "brand_wikidata": "Q80955776"}
    sitemap_urls = ["https://magasins.maisondelaliterie.fr/sitemap_pois.xml"]
    sitemap_rules = [(r".+/details$", "parse_sd")]
