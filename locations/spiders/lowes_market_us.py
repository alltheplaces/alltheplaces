import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class LowesMarketUSSpider(scrapy.Spider):
    name = "lowes_market_us"
    item_attributes = {
        "brand": "Lowe's Market",
        "brand_wikidata": "Q6693107",
        "name": "Lowe's Market",
    }
    allowed_domains = ["www.lowesmarket.com"]
    # The store locator has no sitemap and lists stores by state.
    start_urls = [
        f"https://www.lowesmarket.com/StoreLocator/State/?State={state}&S=" for state in ["TX", "NM", "CO", "AZ", "KS"]
    ]

    def parse(self, response):
        for store_path in set(response.xpath('//a[contains(@href, "StoreLocator/Store/?L=")]/@href').getall()):
            yield response.follow(store_path, callback=self.parse_store)

    def parse_store(self, response):
        ref = response.url.split("L=")[1].split("&")[0]
        url = f"https://www.lowesmarket.com/StoreLocator/Store/?L={ref}"

        branch = response.xpath("//h3/text()").get("")
        branch = branch.split("|", 1)[-1].strip()

        address_lines = [
            line.strip() for line in response.xpath('//p[@class="Address"]/text()').getall() if line.strip()
        ]
        street_address = address_lines[0] if address_lines else None
        city_state_zip = address_lines[1] if len(address_lines) > 1 else None

        item = Feature(
            ref=ref,
            branch=branch,
            street_address=street_address,
            website=url,
        )

        if city_state_zip:
            m = re.match(r"^(?P<city>.+),\s*(?P<state>[A-Z]{2})\s+(?P<zip>\d{5}(-\d{4})?)$", city_state_zip)
            if m:
                item["city"] = m.group("city")
                item["state"] = m.group("state")
                item["postcode"] = m.group("zip")

        phone = response.xpath('//p[@class="PhoneNumber"]//a/text()').get()
        if phone:
            item["phone"] = phone.strip()

        script = response.xpath('//script[contains(text(), "initializeMap")]/text()').get()
        if script:
            if m := re.search(r'initializeMap\("([\-\d.]+)",\s*"([\-\d.]+)"\)', script):
                item["lat"], item["lon"] = m.group(1), m.group(2)

        hours_lines = response.xpath(
            '//dt[contains(text(), "Hours of Operation")]/following-sibling::dd[1]//text()'
        ).getall()
        if hours_lines:
            oh = OpeningHours()
            oh.add_ranges_from_string(", ".join(line.strip() for line in hours_lines if line.strip()))
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
