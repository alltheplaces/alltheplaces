import re

import scrapy

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class LandisSupermarketUSSpider(scrapy.Spider):
    name = "landis_supermarket_us"
    item_attributes = {"brand": "Landis Supermarket", "name": "Landis Supermarket"}
    start_urls = ["https://www.landismarket.com/store-locations/"]

    def parse(self, response):
        for panel in response.xpath('//div[contains(@class,"panel-location")]'):
            item = Feature()
            item["ref"] = item["branch"] = panel.xpath(".//h2/text()").get()
            item["website"] = response.urljoin("#" + panel.attrib["id"])

            address_lines = [
                line.strip() for line in panel.xpath('.//div[contains(@class,"col-md-7")][1]/p[1]//text()').getall()
            ]
            address_lines = [line for line in address_lines if line]
            if len(address_lines) >= 2:
                *street_lines, city_state_zip = address_lines
                item["street_address"] = ", ".join(street_lines)
                if m := re.match(r"^(.*?),\s*([A-Z]{2})\s+(\d{5})$", city_state_zip):
                    item["city"], item["state"], item["postcode"] = m.groups()

            item["phone"] = panel.xpath('.//strong[contains(text(),"Phone")]/following-sibling::a[1]/text()').get()

            if hours_text := panel.xpath('.//strong[contains(text(),"Hours")]/following-sibling::text()[1]').get():
                oh = OpeningHours()
                oh.add_ranges_from_string(hours_text.strip().replace(":", "", 1))
                item["opening_hours"] = oh

            extract_google_position(item, panel)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
