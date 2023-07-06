from scrapy import Request
from scrapy.http import FormRequest

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class PaperSourceUSSpider(AmastyStoreLocatorSpider):
    name = "paper_source_us"
    item_attributes = {"brand": "Paper Source", "brand_wikidata": "Q25000269"}
    start_urls = ["https://www.papersource.com/amlocator/index/ajax/"]

    def start_requests(self):
        formdata = {
            "lat": "0",
            "lng": "0",
            "radius": "",
            "product": "0",
            "category": "0",
            "attributes[0][name]": "3",
            "attributes[0][value]": "",
            "attributes[1][name]": "6",
            "attributes[1][value]": "",
            "sortByDistance": "1",
        }
        for url in self.start_urls:
            yield FormRequest(url=url, formdata=formdata, headers={"X-Requested-With": "XMLHttpRequest"}, method="POST")

    def parse_item(self, item, location, popup_html):
        item["website"] = popup_html.xpath('//a[contains(@class, "amlocator-link")]/@href').get()
        yield Request(url=item["website"], meta={"item": item}, callback=self.add_location_details)

    def add_location_details(self, response):
        item = response.meta["item"]
        item["ref"] = response.xpath(
            '//div[contains(@data-amlocator-js, "location-attributes")]/div[2]/div[3]/div/span/text()'
        ).get()
        item["street_address"] = response.xpath(
            '//div[contains(@class, "amlocator-location-info")]/div[4]/span[2]/text()'
        ).get()
        item["city"] = response.xpath('//div[contains(@class, "amlocator-location-info")]/div[3]/span[2]/text()').get()
        item["postcode"] = response.xpath(
            '//div[contains(@class, "amlocator-location-info")]/div[1]/span[2]/text()'
        ).get()
        item["phone"] = response.xpath(
            '//div[contains(@class, "amlocator-location-info")]/div[contains(@class, "-contact")]/div[1]/a/text()'
        ).get()
        item["email"] = response.xpath(
            '//div[contains(@class, "amlocator-location-info")]/div[contains(@class, "-contact")]/div[2]/a/text()'
        ).get()
        item["image"] = response.xpath('//a[contains(@data-amlocator-js, "location-image")]/@href').get()
        hours_string = " ".join(response.xpath('//div[contains(@class, "amlocator-schedule-table")]//text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
