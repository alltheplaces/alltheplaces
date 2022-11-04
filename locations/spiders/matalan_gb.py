from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MatalanGBSpider(SitemapSpider, StructuredDataSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    sitemap_urls = ["https://www.matalan.co.uk/sitemap/stores.xml"]
    sitemap_rules = [(r"https:\/\/www\.matalan\.co\.uk\/stores\/([-\w]+)$", "parse_sd")]
