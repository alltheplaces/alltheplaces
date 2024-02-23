from scrapy import Spider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class MinimaxAUSpider(Spider):
    name = "minimax_au"
    item_attributes = {"brand": "Minimax", "brand_wikidata": "Q117747075", "extras": Categories.SHOP_HOUSEWARE.value}
    allowed_domains = ["www.minimax.com.au"]
    start_urls = ["https://www.minimax.com.au/pages/store-finder"]

    def parse(self, response):
        for location in response.xpath('//div[@class="storeLocations desktop"]//div[@class="storeWrapper"]'):
            properties = {
                "ref": location.xpath("./@rel").get(),
                "name": location.xpath('.//span[@class="storeName"]/text()').get("").strip(),
                "lat": location.xpath(".//@data-lat").get(),
                "lon": location.xpath(".//@data-lng").get(),
                "addr_full": ", ".join(
                    filter(None, map(str.strip, location.xpath('.//span[@class="detail"][1]/text()').getall()))
                ),
                "phone": location.xpath('.//a[contains(@href, "tel:")]/@href').get("").replace("tel:", ""),
            }
            day_names = list(filter(None, map(str.strip, location.xpath('.//span[@class="day"]//text()').getall())))
            day_times = list(filter(None, map(str.strip, location.xpath('.//span[@class="time"]//text()').getall())))
            hours_string = " ".join([f"{day_name}: {day_time}" for day_name, day_time in zip(day_names, day_times)])
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
