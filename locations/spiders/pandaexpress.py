from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PandaExpressSpider(SitemapSpider, StructuredDataSpider):
    name = "pandaexpress"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    allowed_domains = ["pandaexpress.com"]
    sitemap_urls = ["https://www.pandaexpress.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/\w{2}/[-\w]+/\d+", "parse_sd")]
    time_format = "%I:%M %p"
