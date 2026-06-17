import re

from scrapy import Request, Spider

from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone


class HalfordsNLSpider(Spider):
    name = "halfords_nl"
    item_attributes = {"brand": "Halfords", "brand_wikidata": "Q3398786"}
    start_urls = ["https://www.halfords.nl/halfords-winkels/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        store_urls = response.xpath('//*[@class="amlocator-store-list"]//*[@href]/@href').getall()
        for store in store_urls:
            yield Request(url=store, callback=self.parse_store)

    def parse_store(self, response):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["name"] = response.xpath("//*[@data-ui-id]/text()").get()
        item = self.get_lat_long(response, item)
        extract_phone(item, response)
        extract_email(item, response)
        item = self.get_address(response, item)
        yield item

    def get_lat_long(self, response, item):
        script = response.xpath('//script[contains(text(), "myLatLng")]/text()').get()
        lat_lng = re.search(r"lat: ([\d.-]+), lng: ([\d.-]+)", script)
        if lat_lng:
            item["lat"] = float(lat_lng.group(1))
            item["lon"] = float(lat_lng.group(2))
        return item

    def get_address(self, response, item):
        street_address, city_postcode, _ = response.xpath(
            '//*[@class="amlocator-block -contact mb-6"]/div/span/text()'
        ).getall()
        item["street_address"] = street_address
        postcode, city = city_postcode.split(", ")
        item["city"] = city
        item["postcode"] = postcode

        return item

    def get_opening_hours(self, response, item):
        oh = OpeningHours()
        days = response.xpath('//*[@class="amlocator-cell -day"]/text()').getall()
        hours = response.xpath('//*[@class="amlocator-cell -time"]/text()').getall()
        for day, hour in zip(days, hours):
            if "-" in hour:
                oh.add_ranges_from_string(ranges_string=day + " " + hour, days=DAYS_NL, delimiters=" - ")
        item["opening_hours"] = oh.as_opening_hours()
        return item
