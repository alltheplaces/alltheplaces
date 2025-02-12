from html import unescape

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_IT, OpeningHours
from locations.spiders.virgin_active_bw_na_za import VIRGIN_ACTIVE_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class VirginActiveITSpider(CrawlSpider, StructuredDataSpider):
    name = "virgin_active_it"
    item_attributes = VIRGIN_ACTIVE_SHARED_ATTRIBUTES
    allowed_domains = ["www.virginactive.it"]
    start_urls = ["https://www.virginactive.it/club"]
    rules = [
        Rule(LinkExtractor(allow=r"/club/[-\w]+/[-\w]+$"), follow=False, callback="parse"),
    ]
    time_format = "%H.%M"
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data):
        item["branch"] = item.pop("name")
        item["image"] = item["image"].split("?")[0]
        item["opening_hours"] = OpeningHours()
        for spec in ld_data.get("openingHoursSpecification"):
            for day in spec["dayOfWeek"]:
                item["opening_hours"].add_ranges_from_string(
                    f"{unescape(day)} {spec['opens']}-{spec['closes']}", DAYS_IT
                )
        yield item
