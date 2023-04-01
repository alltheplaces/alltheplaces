import re

from scrapy import FormRequest, Request

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class JourneysSpider(StructuredDataSpider):
    name = "journeys"
    item_attributes = {"brand": "Journeys", "brand_wikidata": "Q61994838"}
    start_urls = ["https://www.journeys.com/stores", "https://www.journeys.ca/stores"]
    requires_proxy = True
    time_format = "%I:%M %p"

    def parse(self, response, **kwargs):
        for state in response.xpath('//select[@name="StateOrProvince"]/option/@value').getall():
            if state:
                yield FormRequest(
                    url=response.url,
                    formdata={"StateOrProvince": state, "Mode": "search"},
                    callback=self.parse_store_list,
                )

    def parse_store_list(self, response):
        for url in response.xpath('//div[@class="store-heading"]//a[1]/@href').getall():
            yield Request(url=response.urljoin(url), callback=self.parse_sd)

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["openingHoursSpecification"] = []
        for rule in ld_data["address"].pop("openingHours", []):
            if m := re.match(r"(\w+): (\d+:\d+ [AP]M) - (\d+:\d+ [AP]M)", rule):
                ld_data["openingHoursSpecification"].append(
                    {"dayOfWeek": m.group(1), "opens": m.group(2), "closes": m.group(3)}
                )

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["brand"], item["ref"] = item.pop("name").split(" #")

        apply_category(Categories.SHOP_SHOES, item)

        yield item
