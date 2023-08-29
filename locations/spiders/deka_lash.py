from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DekaLashSpider(SitemapSpider, StructuredDataSpider):
    name = "deka_lash"
    sitemap_urls = ["https://dekalash.com/page-sitemap.xml"]
    sitemap_rules = [(r"/find-a-studio/.+/.+/$", "parse")]
    wanted_types = ["BeautySalon"]
