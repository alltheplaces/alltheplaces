import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone


class FirstHotelsSpider(scrapy.Spider):
    name = "first_hotels"
    item_attributes = {"brand": "First Hotels", "brand_wikidata": "Q11969007"}
    start_urls = ["https://www.firsthotels.com/general-info/about-first-hotels/map-of-hotels/"]

    def parse(self, response):
        hotels = json.loads(response.xpath('//*[@class="allhotels"]/div/@data-pois').get())
        for hotel in hotels:
            item = Feature()
            item["ref"] = hotel["id"]
            item["name"] = hotel["name"]
            item["lon"] = hotel["longitude"]
            item["lat"] = hotel["latitude"]
            item["website"] = "https://www.firsthotels.com" + hotel["url"]
            yield scrapy.Request(url=item["website"], callback=self.parse_hotel, cb_kwargs={"item": item})

    def parse_hotel(self, response, item):
        tels = response.xpath('//*[@itemprop="telephone"]/text()').getall()
        for tel in tels:
            if "Contact the hotel" in tel:
                item["phone"] = tel.replace("Contact the hotel", "").strip()
                break
        extract_email(item, response)
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["city"] = response.xpath('//*[@itemprop="addressLocality"]/text()').get()
        item["country"] = response.xpath('//*[@itemprop="addressCountry"]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        apply_category(Categories.HOTEL, item)

        yield item
