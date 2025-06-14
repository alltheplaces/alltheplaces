from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CornerBakeryCafeUSSpider(CrawlSpider, StructuredDataSpider):
    name = "corner_bakery_cafe_us"
    item_attributes = {"brand": "Corner Bakery", "brand_wikidata": "Q5171598"}
    allowed_domains = ["cornerbakerycafe.com"]
    start_urls = [
        "https://cornerbakerycafe.com/locations/all",
    ]
    rules = [Rule(LinkExtractor(allow=r"/location/[-\w]+/?$"), callback="parse_sd")]
    wanted_types = [["Restaurant", "CafeOrCoffeeShop"]]
    drop_attributes = {"facebook", "twitter"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url
        if "opening on" in response.xpath('//*[@id="loc-about-this"]/p/text()').get("").lower():  # coming soon
            return
        item["branch"] = item.pop("name", "")
        services = response.xpath('//*[@class="loc-amenities"]/span/text()').getall()
        apply_yes_no(Extras.WIFI, item, "Wifi" in services)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in services)
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in services)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "Patio/Outdoor Seating" in services)
        yield item
