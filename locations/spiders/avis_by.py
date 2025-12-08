import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.avis import AvisSpider


class AvisBYSpider(scrapy.Spider):
    name = "avis_by"
    item_attributes = AvisSpider.item_attributes
    start_urls = ["https://avis.by/en/"]

    def parse(self, response, **kwargs):
        for location in response.xpath('//*[@id="start-map-tab"]//li[@data-id]'):
            item = Feature()
            item["ref"] = location.xpath("./@data-id").get()
            location_details = location.xpath('.//*[@class="details-block"]')
            address = (
                location_details.xpath('.//span[@lang="en-US"]/text()').get()
                or location_details.xpath("./text()").get()
            )
            item["street_address"], item["phone"] = address.split("+") if "+" in address else (address, None)
            item["street_address"] = item["street_address"].replace("Adress:", "")
            if "available on request" in item["street_address"]:
                continue
            if not item["phone"]:
                if phone_match := re.search(r"After working hours on request\s([-+()\s\d]+)", location_details.get()):
                    item["phone"] = phone_match.group(1)
            item["name"] = location.xpath('.//*[@class="item-block"]/text()').get()
            item["website"] = response.url
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location_details.get())
            yield item
