from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
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

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = response.xpath('//*[@class="location-name"]/text()').get()
        yield item
