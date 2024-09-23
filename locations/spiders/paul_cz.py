from scrapy import Spider

from locations.hours import DAYS_CZ, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES


class PaulCZSpider(Spider):
    name = "paul_cz"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    start_urls = ["https://www.paul-cz.com/obchody/"]

    def parse(self, response):
        for location in response.xpath('.//article[contains(@class, "store")]'):
            item = Feature()
            item["ref"] = location.xpath("@data-store_id").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["branch"] = location.xpath(".//h2/span/text()").get()
            item["phone"] = location.xpath('.//div[contains(@class, "tel")]/text()').get()
            item["addr_full"] = clean_address(
                location.xpath('.//div[contains(@class, "address")]/span/text()').getall()
            )

            item["opening_hours"] = OpeningHours()
            for day in location.xpath('.//div[contains(@class, "opening-hours")]/div'):
                item["opening_hours"].add_ranges_from_string(day.xpath("string(.)").get(), days=DAYS_CZ)

            yield item
