from scrapy import Spider

from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class WebbersZASpider(Spider):
    name = "webbers_za"
    start_urls = ["https://www.webbers.co.za/storelocator"]
    item_attributes = {
        "brand": "Webbers",
        "brand_wikidata": "Q116619741",
    }

    def parse(self, response):
        for province in response.xpath('.//div[@class="store-locator__region-container"]'):
            province_name = province.xpath('.//div[@class="store-locator__region-name"]/text()').get().strip()
            for city in province.xpath('.//div[@class="store-locator__city-name"]'):
                city_name = city.xpath('.//div[@class="city-name"]/text()').get().strip()
                for location in city.xpath('.//div[@class="store-locator__item"]'):
                    item = Feature()
                    item["branch"] = location.xpath('.//div[@class="store-locator__name"]/text()').get().strip()
                    item["lat"], item["lon"] = url_to_coords(
                        location.xpath('.//a[contains(@href,"maps.google.com")]/@href').get()
                    )

                    item["addr_full"] = clean_address(
                        location.xpath('.//div[@class="store-locator__address"]/text()').getall()
                    )
                    item["city"] = city_name
                    item["state"] = province_name

                    item["phone"] = location.xpath('.//div[@class="phone"]/text()').get().strip()
                    item["website"] = location.xpath('.//a[@class="info"]/@href').get()
                    item["ref"] = item["website"]

                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_ranges_from_string(
                        location.xpath('string(.//div[@class="store-locator__hours"])').get()
                    )
                    yield item
