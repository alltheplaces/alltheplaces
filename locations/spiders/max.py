import urllib

from scrapy import FormRequest, Spider

from locations.categories import apply_yes_no
from locations.items import Feature


class MaxSpider(Spider):
    name = "max"
    item_attributes = {"brand": "Max", "brand_wikidata": "Q1912172"}
    start_urls = ["https://www.max.se/hitta-max/restauranger/"]

    COUNTRY_MAP = {"da": "DK", "no": "NO", "pl": "PL", "sv": "SE"}

    def parse(self, response, **kwargs):
        token = response.xpath('//input[@name="__RequestVerificationToken"]/@value').get()
        for country_ref in response.xpath('//select[@id="select-country"]/option/@value').getall():
            yield FormRequest(
                url="https://www.max.se/hitta-max/restauranger/",
                formdata={"country": country_ref, "__RequestVerificationToken": token},
                callback=self.parse_locations,
                cb_kwargs={"cc": self.COUNTRY_MAP[country_ref]},
            )

    def parse_locations(self, response, cc):
        for location in response.xpath('//a[@class="o-restaurant-list__item js-restaurant-item"]'):
            item = Feature()
            item["ref"] = item["website"] = urllib.parse.urljoin(response.url, location.xpath("./@href").get())
            item["lat"], item["lon"] = location.xpath("./@data-coords").get().split(",")
            item["name"] = location.xpath('.//h2[@class="o-restaurant-list__heading"]/text()').get()
            item["street_address"] = location.xpath('.//div[@class="o-restaurant-list__location"]/span/text()').get()
            item["city"] = location.xpath('.//div[@class="o-restaurant-list__city"]/text()').get()
            item["postcode"] = location.xpath("./@data-postal").get().replace(item["city"], "").strip()
            item["country"] = cc

            apply_yes_no(
                "drive_through",
                item,
                location.xpath('.//div[@class="o-restaurant-list__drive-through"]/text()').get() == "Je",
            )

            yield item
