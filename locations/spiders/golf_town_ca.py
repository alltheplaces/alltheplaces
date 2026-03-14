from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GolfTownCASpider(SitemapSpider, StructuredDataSpider):
    name = "golf_town_ca"
    item_attributes = {"brand": "Golf Town", "brand_wikidata": "Q112966691"}
    sitemap_urls = ["https://locations.golftown.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.golftown.com/golf-town-[-\w]+$", "parse_sd")]
