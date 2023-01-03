from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PFChangsSpider(SitemapSpider, StructuredDataSpider):
    name = "pf_changs"
    allowed_domains = ["www.pfchangs.com"]
    sitemap_urls = ["https://www.pfchangs.com/locations/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+/[-\w]+/[-\w]+/[-\w]+/[-\w]+.html$", "parse_sd")]
    wanted_types = ["Restaurant"]
