import chompjs
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class HSamuelGBSpider(CrawlSpider, StructuredDataSpider):
    name = "h_samuel_gb"
    item_attributes = {"brand": "H.Samuel", "brand_wikidata": "Q5628558"}
    start_urls = ["https://www.hsamuel.co.uk/store-finder/view-stores/GB%20Region"]
    rules = [Rule(LinkExtractor(allow="/store/"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")

        data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "storeInformation")]/text()').get())
        item["street_address"] = merge_address_lines([data["line1"], data["line2"]])

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if times := data["openings"].get(f"{day}:"):
                if times == "Closed":
                    continue
                start_time, end_time = times.split(" - ")
                item["opening_hours"].add_range(day, start_time, end_time, time_format="%I:%M %p")

        yield item
