from urllib.parse import unquote

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class TheCrazyStoreSpider(Spider):
    name = "the_crazy_store"
    item_attributes = {"brand": "The Crazy Store", "brand_wikidata": "Q116620808"}
    start_urls = ["https://www.crazystore.co.za/store-finder"]

    def parse(self, response):
        for location in response.xpath('.//div[contains(@class,"geolocation-location")]'):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["name"] = location.xpath('.//div[contains(@class,"field--name-name")]/text()').get()
            item["phone"] = unquote(
                location.xpath('.//div[contains(@class,"field field--name-field-phone")]/.//a/@href').get("")
            )
            item["website"] = (
                "https://www.crazystore.co.za/store-locator/#" + location.xpath(".//article/@data-marker").get()
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                " ".join(
                    location.xpath(
                        './/div[contains(@class,"field--name-field-trading-hours-weekdays")]/div/text()'
                    ).getall()
                )
                .replace(")", "")
                .replace("Weekdays (", "")
            )
            for day in ["fridays", "weekend-sat", "weekend-sun"]:
                item["opening_hours"].add_ranges_from_string(
                    " ".join(
                        location.xpath(
                            f'.//div[contains(@class,"field--name-field-trading-hours-{day}")]/div/text()'
                        ).getall()
                    ),
                )
            yield item
