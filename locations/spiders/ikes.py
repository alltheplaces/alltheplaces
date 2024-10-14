from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
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
        services = [
            service.strip().lower() for service in response.xpath('//*[@class="location-services"]/li/text()').getall()
        ]
        apply_yes_no(Extras.DELIVERY, item, "delivery" in services)
        apply_yes_no(Extras.INDOOR_SEATING, item, "dine-in" in services)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "patio" in services)
        yield item
