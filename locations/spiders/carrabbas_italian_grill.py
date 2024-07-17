from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CarrabbasItalianGrillSpider(SitemapSpider, StructuredDataSpider):
    name = "carrabbas_italian_grill"
    allowed_domains = ["carrabbas.com"]
    item_attributes = {
        "brand": "Carrabba's Italian Grill",
        "brand_wikidata": "Q5045999",
    }
    sitemap_urls = ["https://locations.carrabbas.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/locations\.carrabbas\.com\/[-\w]+\/[-.'\w]+\/[-.'\w]+$",
            "parse_sd",
        )
    ]
    wanted_types = ["Restaurant"]
