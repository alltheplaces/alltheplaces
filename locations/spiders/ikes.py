from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class IkesSpider(SitemapSpider, StructuredDataSpider):
    name = "ikes"
    item_attributes = {
        "brand": "Ike's Love & Sandwiches",
        "brand_wikidata": "Q112028897",
    }
    sitemap_urls = ["https://locations.ikessandwich.com/robots.txt"]
    sitemap_rules = [
        (
            r"https://locations.ikessandwich.com/[a-z]{2}/[-\w]+/[-\w]+",
            "parse_sd",
        ),
    ]
