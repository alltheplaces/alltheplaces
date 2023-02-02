from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class MaxolIESpider(SitemapSpider, StructuredDataSpider):
    name = "maxol_ie"
    item_attributes = {"brand": "Maxol", "brand_wikidata": "Q3302837", "extras": Categories.FUEL_STATION.value}
    sitemap_urls = ["https://stations.maxol.ie/sitemap.xml"]
    sitemap_rules = [(r"\.ie\/[-\w]+\/[-.\w]+\/[-\/\w]+$", "parse_sd")]
