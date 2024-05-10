from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class AmartFurnitureAUSpider(Spider):
    name = "amart_furniture_au"
    item_attributes = {"brand": "Amart Furniture", "brand_wikidata": "Q114119879"}
    allowed_domains = ["www.amartfurniture.com.au"]
    start_urls = [
        "https://www.amartfurniture.com.au/store-region/QLD",
        "https://www.amartfurniture.com.au/store-region/NSW",
        "https://www.amartfurniture.com.au/store-region/VIC",
        "https://www.amartfurniture.com.au/store-region/WA",
        "https://www.amartfurniture.com.au/store-region/TAS",
        "https://www.amartfurniture.com.au/store-region/SA",
        "https://www.amartfurniture.com.au/store-region/NT",
        "https://www.amartfurniture.com.au/store-region/ACT",
    ]

    def parse(self, response):
        for location in response.xpath('//div[contains(@class, "card-body")]'):
            properties = {
                "ref": location.xpath(".//@data-store-id").get(),
                "name": location.xpath('.//h5[@class="store-name"]/text()').get(),
                "addr_full": clean_address(location.xpath('.//p[@class="address"]//text()').getall()),
                "phone": location.xpath('.//a[@class="phone"]/@href').get("").replace("tel:", ""),
                "email": location.xpath('.//a[@class="email"]/@href').get("").replace("mailto:", ""),
                "website": "https://www.amartfurniture.com.au"
                + location.xpath('.//h5[@class="store-name"]/ancestor::*[self::a][1]/@href').get(),
            }
            properties["lat"], properties["lon"] = (
                location.xpath('.//button[contains(@onclick, "https://maps.google.com/?daddr=")]/@onclick')
                .get()
                .split("?daddr=", 1)[1]
                .split("'", 1)[0]
                .split(",", 1)
            )
            hours_string = " ".join(filter(None, location.xpath('.//div[@class="store-hours"]//text()').getall()))
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
