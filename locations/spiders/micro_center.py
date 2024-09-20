import scrapy

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories


class MicroCenterSpider(StructuredDataSpider):
    name = "micro_center"
    item_attributes = {"brand": "Micro Center", "brand_wikidata": "Q6839153", "extras": Categories.SHOP_COMPUTER.value }
    allowed_domains = ["www.microcenter.com"]
    start_urls = ["https://www.microcenter.com/site/stores/default.aspx"]
    wanted_types = ["ComputerStore"]

    def parse(self, response):
        for url in response.xpath('//div[@class="location-container"]//a/@href').extract():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data):
        if "openingHoursSpecification" in ld_data:
            opening_hours = OpeningHours()
            for spec in ld_data["openingHoursSpecification"]:
                day = spec["dayOfWeek"][:2]
                open_time = spec["opens"] + ":00"
                close_time = spec["closes"] + ":00"
                opening_hours.add_range(day, open_time, close_time)

            item["opening_hours"] = opening_hours
        item["ref"] = response.url

        yield item
