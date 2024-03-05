from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ArcaplanetITSpider(SitemapSpider, StructuredDataSpider):
    name = "arcaplanet_it"
    item_attributes = {"brand": "Arcaplanet", "brand_wikidata": "Q105530937"}
    sitemap_urls = ["https://negozi.arcaplanet.it/sitemap.xml"]
    sitemap_rules = [(r"it/[^/]+/\w\w/.+$", "parse")]
    wanted_types = ["PetStore"]
