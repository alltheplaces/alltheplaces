from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class IxinaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ixina_fr"
    item_attributes = {"brand": "Ixina", "brand_wikidata": "Q3156424"}
    sitemap_urls = ["https://magasins.ixina.fr/sitemap.xml"]
    sitemap_rules = [
        (r"https://magasins.ixina.fr/fr/magasins/[\w-]+/[\w-]+/[\w-]+", "parse"),
    ]
