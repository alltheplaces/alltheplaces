from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class StateFarmUSSpider(SitemapSpider, StructuredDataSpider):
    name = "state_farm_us"
    item_attributes = {"brand": "State Farm", "brand_wikidata": "Q2007336", "country": "US"}
    sitemap_urls = ["https://www.statefarm.com/sitemap-agents.xml"]
    sitemap_rules = [(r"/agent/us/\w\w/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["InsuranceAgency"]
