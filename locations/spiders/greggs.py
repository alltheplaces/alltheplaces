from scrapy import Spider

from locations.items import GeojsonPointItem


class GreggsSpider(Spider):
    name = "greggs"
    item_attributes = {"brand": "Greggs", "brand_wikidata": "Q3403981"}
    start_urls = ["https://production-digital.greggs.co.uk/api/v1.0/shops"]

    def parse(self, response):
        for store in response.json():
            item = GeojsonPointItem()

            item["lat"] = store["address"]["latitude"]
            item["lon"] = store["address"]["longitude"]
            item["name"] = store["shopName"]
            item["housenumber"] = store["address"]["houseNumberOrName"]
            item["street"] = store["address"]["streetName"]
            item["city"] = store["address"]["city"]
            item["postcode"] = store["address"]["postCode"]
            item["country"] = store["address"]["country"]
            item["phone"] = store["address"]["phoneNumber"]
            item["ref"] = store["shopCode"]

            yield item
