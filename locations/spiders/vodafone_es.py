from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class VodafoneEsSpider(SitemapSpider, StructuredDataSpider):
    name = "vodafone_es"
    item_attributes = {
        "brand": "Vodafone",
        "brand_wikidata": "Q122141",
    }
    allowed_domains = ["vodafone.es"]
    sitemap_urls = ["https://tiendas.vodafone.es/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/tiendas.vodafone.es\/tiendas\/.+\/.+\/.+", "parse_sd")]

    wanted_types = ["MobilePhoneStore"]
