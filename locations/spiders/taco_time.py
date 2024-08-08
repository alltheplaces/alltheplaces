from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TacoTimeSpider(SitemapSpider, StructuredDataSpider):
    name = "taco_time"
    item_attributes = {
        "brand": "Taco Time",
        "brand_wikidata": "Q7673969",
    }
    sitemap_urls = ["https://www.tacotime.com/sitemap.xml"]
    sitemap_rules = [
        (r"/stores/", "parse_sd"),
    ]
