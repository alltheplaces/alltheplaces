from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BlainsFarmAndFleetUSSpider(SitemapSpider, StructuredDataSpider):
    name = "blains_farm_and_fleet_us"
    item_attributes = {"brand": "Blain's Farm & Fleet", "brand_wikidata": "Q4923906"}
    allowed_domains = ["www.farmandfleet.com"]
    sitemap_urls = ["https://www.farmandfleet.com/sitemap_stores.xml.gz"]
    sitemap_rules = [(r"\/stores\/[\w\-]+\/$", "parse_sd")]
    time_format = "%H:%M:%S"
    requires_proxy = True
