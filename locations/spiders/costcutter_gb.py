from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CostcutterGBSpider(SitemapSpider, StructuredDataSpider):
    name = "costcutter_gb"
    item_attributes = {"brand": "Costcutter", "brand_wikidata": "Q5175072"}
    allowed_domains = ["costcutter.co.uk"]
    sitemap_urls = ["https://store-locator.costcutter.co.uk/sitemap.xml"]
    sitemap_rules = [(r"uk/en-gb/[^/]+/[^/]+/(\d+)$", "parse")]
    wanted_types = ["FoodEstablishment"]
    drop_attributes = {"image"}
    search_for_facebook = False
    search_for_twitter = False
