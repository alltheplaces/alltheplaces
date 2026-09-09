import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class SimonsonStationStoresUSSpider(scrapy.Spider):
    name = "simonson_station_stores_us"
    item_attributes = {"brand": "Simonson Station Stores"}
    start_urls = ["https://gosimonson.com/home/locations/"]

    def parse(self, response, **kwargs):
        # Each store is rendered as an Elementor column containing an address,
        # a phone number and a "Location Info" button linking to the store's
        # own page. There is no structured data (JSON-LD) or geocoded map
        # embed anywhere on this WordPress/Elementor site, so no coordinates
        # are available for this spider.
        buttons = response.xpath(
            '//a[contains(@class, "elementor-button-link")][.//span[normalize-space(text())="Location Info"]]'
        )
        for button in buttons:
            href = button.xpath("@href").get()
            column = button.xpath('ancestor::div[contains(@class, "elementor-column")][1]')

            address_lines = [line.strip() for line in column.xpath(".//p//text()").getall() if line.strip()]
            if len(address_lines) < 2:
                continue

            street_address, city_state_zip = address_lines[0], address_lines[1]

            phone_texts = column.xpath(
                './/i[contains(@class, "fa-phone")]/ancestor::div[contains(@class, "elementor-icon-box-wrapper")]//h3//text()'
            ).getall()
            phone = next((t.strip() for t in phone_texts if t.strip()), None)

            item = Feature()
            item["name"] = self.item_attributes["brand"]
            item["ref"] = response.urljoin(href)
            item["website"] = response.urljoin(href)
            item["street_address"] = street_address
            if phone:
                item["phone"] = phone

            if m := re.match(r"^(.*),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", city_state_zip):
                city = m.group(1)
                if city == "Wiliston":  # typo on the source site's Williston listing
                    city = "Williston"
                item["city"], item["state"], item["postcode"] = city, m.group(2), m.group(3)
                item["branch"] = item["city"]
            else:
                item["addr_full"] = f"{street_address}, {city_state_zip}"

            apply_category(Categories.FUEL_STATION, item)

            yield item
