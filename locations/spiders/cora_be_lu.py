import urllib.parse

from scrapy import Request, Spider

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CoraBELUSpider(Spider):
    # For BE and LU only
    name = "cora_be_lu"
    item_attributes = {"brand": "Cora", "brand_wikidata": "Q686643"}
    start_urls = ["https://www.cora.be/fr/choix-du-magasin"]

    def parse(self, response):
        stores = response.xpath('//*[@class="ca-PinsPanel-btn"]/a/@href').getall()
        for store in stores:
            yield Request(url=store, callback=self.parse_store)

    def parse_store(self, response):
        store_info = response.xpath('//*[@class="ca-MiscStore"]')
        street_address, postcode_city, tel = store_info.xpath("./address/text()").getall()
        item = Feature()
        item["ref"] = response.url.split("/")[-1]
        item["street_address"] = clean_address(street_address)
        item["postcode"] = postcode_city.strip().split(" ", maxsplit=1)[0]
        item["city"] = postcode_city.strip().split(" ", maxsplit=1)[1]
        item["housenumber"] = item["street_address"].split(", ")[1]
        item["phone"] = tel.replace("Tél :", "").strip()
        item["opening_hours"] = self.parse_opening_hours(store_info)
        item["website"] = response.url
        item["name"] = "Cora " + item["city"]
        item["country"] = urllib.parse.urlparse(response.url).netloc.split(".")[-1].upper()
        yield item

    def parse_opening_hours(self, store_info):
        opening_hours = OpeningHours()
        timetable = store_info.xpath('.//*[@class="ca-MiscStore-openingList"]/li')
        for row in timetable:
            day = row.xpath('.//*[@class="ca-MiscStore-openingDay"]/text()').get()
            hours = row.xpath('.//*[@class="ca-MiscStore-openingHours"]/text()').get().replace("h", ":")
            opening_hours.add_ranges_from_string(ranges_string=day + hours, days=DAYS_FR, delimiters=[" > ", " - "])
        return opening_hours.as_opening_hours()
