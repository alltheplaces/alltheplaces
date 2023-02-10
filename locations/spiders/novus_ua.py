from scrapy import FormRequest, Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class NovusUASpider(Spider):
    name = "novus_ua"
    item_attributes = {"brand": "Novus", "brand_wikidata": "Q116748340"}
    start_urls = ["https://novus.ua/"]

    def parse(self, response, **kwargs):
        for city in response.xpath('//select[@id="select-city"]/option'):
            yield FormRequest(
                url="https://novus.ua/api/popup/shops",
                formdata={"cityId": city.xpath("./@value").get()},
                headers={"X-Requested-With": "XMLHttpRequest"},
                cb_kwargs={"city": city.xpath("./text()").get().strip()},
                callback=self.parse_city,
            )

    def parse_city(self, response, city, **kwargs):
        if response.json()["errors"]:
            return

        for location in response.json()["data"].values():
            item = Feature()
            item["ref"] = location["entity_id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["street_address"] = location["name"]
            item["city"] = city

            item["opening_hours"] = OpeningHours()
            start_time, end_time = location["opening_hours"].replace(".", ":").replace(" - ", "-").split("-")
            item["opening_hours"].add_days_range(DAYS, start_time, end_time)

            yield item
