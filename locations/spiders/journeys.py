import re

from scrapy import FormRequest, Request

from locations.categories import Categories, apply_category
from locations.pipelines.address_clean_up import merge_address_lines
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
        _, item["ref"] = item["name"].split(" #", 1)
        if item["name"].startswith("JOURNEYS KIDZ"):
            item["name"] = "Journeys Kidz"
        elif item["name"].startswith("JOURNEYS"):
            item["name"] = "Journeys"
        elif item["name"].startswith("UNDERGROUND"):
            item["name"] = "Underground by Journeys"
        elif item["name"].startswith("SHI"):
            item["name"] = "Shi by Journeys"
        else:
            self.logger.error("Unknown name: {}".format(item["name"]))

        item["street_address"] = merge_address_lines(
            [
                response.xpath('//div[@itemprop="address"]/p[1]/text()').get(),
                response.xpath('//div[@itemprop="address"]/p[2]/text()').get(),
            ]
        )

        apply_category(Categories.SHOP_SHOES, item)

        yield item
