from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_EN
from locations.structured_data_spider import StructuredDataSpider


class LeeannChinUSSpider(CrawlSpider, StructuredDataSpider):
    name = "leeann_chin_us"
    item_attributes = {
        "brand": "Leeann Chin",
        "brand_wikidata": "Q6515716",
    }
    start_urls = ["https://www.leeannchin.com/locations"]
    wanted_types = ["Restaurant"]
    rules = [
        Rule(LinkExtractor(allow=r"restaurant/"), callback="parse_sd"),
    ]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "openingHours" in ld_data:
            item["opening_hours"].add_ranges_from_string(ld_data["openingHours"], days=DAYS_EN)

        return super().post_process_item(item, response, ld_data, **kwargs)
