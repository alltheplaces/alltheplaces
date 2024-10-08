from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HarvesterGBSpider(SitemapSpider, StructuredDataSpider):
    name = "harvester_gb"
    item_attributes = {"brand": "Harvester", "brand_wikidata": "Q5676915"}
    sitemap_urls = ["https://www.harvester.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.harvester\.co\.uk\/restaurants\/[\w]+\/[\w]+$", "parse_sd")]
    wanted_types = ["Restaurant"]
