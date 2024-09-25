import re

import scrapy

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class Fournos(scrapy.Spider):
    name = "fournos_za"
    start_urls = ["https://www.fournos.co.za/find-us.php"]
    item_attributes = {
        "brand": "Fournos Bakery",
        "brand_wikidata": "Q116740976",
    }

    def parse(self, response):
        for location in response.xpath('.//div[contains(@class, "modal")][contains(@id, "storeInfo")]'):
            item = Feature()
            extract_google_position(item, location)
            item["ref"] = location.xpath("@id").get()
            item["branch"] = location.xpath(".//h4/text()").get()
            item["phone"] = location.xpath('.//a[contains(@href, "tel:")]/@href').get()
            item["email"] = location.xpath('.//a[contains(@onclick, "mailto:")]/text()').get()

            if item["branch"] == "Head Office":
                apply_category(Categories.OFFICE_COMPANY, item)
                item["addr_full"] = clean_address(location.xpath('.//div[contains(@id, "store")]/p[2]/text()').getall())
                item["opening_hours"] = OpeningHours()
                hours_string = " ".join(location.xpath('.//div[contains(@id, "store")]/p[3]/text()').getall())
                hours_string = re.sub(r"(\d)h(\d)", r"\1:\2", hours_string)
                item["opening_hours"].add_ranges_from_string(hours_string)
                yield item
            else:
                item["addr_full"] = clean_address(location.xpath('.//div[contains(@id, "store")]/p[1]/text()').getall())
                item["opening_hours"] = OpeningHours()
                hours_string = " ".join(location.xpath('.//div[contains(@id, "store")]/p[2]/text()').getall())
                hours_string = re.sub(r"(\d)h(\d)", r"\1:\2", hours_string)
                item["opening_hours"].add_ranges_from_string(hours_string)
                yield item
