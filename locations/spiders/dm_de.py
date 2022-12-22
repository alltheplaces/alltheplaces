from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DrogerieMarktSpider(SitemapSpider, StructuredDataSpider):
    name = "dm_de"
    item_attributes = {"brand": "dm", "brand_wikidata": "Q266572"}
    sitemap_urls = ["https://store-data-service.services.dmtech.com/sitemap/DE"]
    sitemap_rules = [(r"www.dm.de/store/", "parse_sd")]
    download_delay = 0.5
