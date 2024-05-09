import re

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class ZambreroAUSpider(Spider):
    name = "zambrero_au"
    item_attributes = {"brand": "Zambrero", "brand_wikidata": "Q18636431", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["www.zambrero.com.au"]

    def start_requests(self):
        yield Request(url=f"https://{self.allowed_domains[0]}/locations", callback=self.parse_location_list)

    def parse_location_list(self, response):
        location_urls = response.xpath('//div[@data-location-id]//a[@title="Order & Store Info"]/@href').getall()
        for location_url in location_urls:
            yield Request(url=location_url, callback=self.parse_location)

    def parse_location(self, response):
        properties = {
            "ref": response.xpath("//@data-location-id").get(),
            "name": re.sub(r"\s+", " ", response.xpath("//div[@data-location-id]/h4/text()").get()).strip(),
            "lat": response.xpath("//@data-lat").get(),
            "lon": response.xpath("///@data-lng").get(),
            "addr_full": clean_address(
                " ".join(response.xpath('//div[@data-location-id]//span[contains(@class, "address")]/text()').getall())
            ),
            "phone": response.xpath('//a[contains(@class, "phone")]/@href').get().replace("tel:", ""),
            "email": response.xpath('//a[contains(@href, "mailto:")]/@href').get().replace("mailto:", ""),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        if "Temporarily Closed" in properties["name"]:
            return
        if properties["phone"] == "0":
            properties.pop("phone")

        hours_text = re.sub(
            r"\s+", " ", " ".join(response.xpath('//div[contains(@class, "hours-item")]/span/text()').getall())
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)

        # Some store names and URLs contain "Opening Soon" but numerous of
        # these are already open and the URL hasn't been changed. A more
        # reliable way of knowing a store is not yet open is that it has
        # no opening hours specified.
        if not properties["opening_hours"].as_opening_hours():
            return

        yield Feature(**properties)
