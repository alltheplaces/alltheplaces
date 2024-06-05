from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class WheelWorksUSSpider(CrawlSpider, StructuredDataSpider):
    name = "wheel_works_us"
    item_attributes = {"brand": "Wheel Works", "brand_wikidata": "Q121088283"}
    allowed_domains = ["www.wheelworks.net", "local.wheelworks.net"]
    start_urls = ["https://www.wheelworks.net/site-map/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/local\.wheelworks\.net/.+"),
            callback="parse_sd",
            follow=False,
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        additional_properties = {
            prop["propertyID"]: prop["value"]
            for prop in ld_data.get("additionalProperty", [])
            if "propertyID" in prop and "value" in prop
        }
        item["image"] = additional_properties.get("storeImage")
        item["street"] = additional_properties.get("street")

        hours = OpeningHours()
        hours.from_linked_data(ld_data, "%H:%M:%S")
        item["opening_hours"] = hours.as_opening_hours()
        yield item
