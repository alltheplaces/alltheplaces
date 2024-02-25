from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class SinclairUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sinclair_us"
    item_attributes = {"brand": "Sinclair", "brand_wikidata": "Q1290900", "extras": Categories.FUEL_STATION.value}
    sitemap_urls = ["https://stations.sinclairoil.com/robots.txt"]
    sitemap_rules = [(r"\.com/\w\w/[^/]+/[^/]+$", "parse")]
    wanted_types = ["GasStation"]
