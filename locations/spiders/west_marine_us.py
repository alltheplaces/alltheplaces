from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WestMarineUSSpider(SitemapSpider, StructuredDataSpider):
    name = "west_marine_us"
    item_attributes = {"brand": "West Marine", "brand_wikidata": "Q7985852"}
    sitemap_urls = ["https://www.westmarine.com/sitemap-new_stores_sitemap.xml"]
    sitemap_rules = [(r"stores/(.*)/$", "parse_sd")]
    wanted_types = ["Store"]
