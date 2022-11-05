import scrapy

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class PizzaExpressGBSpider(scrapy.Spider):
    name = "pizza_express_gb"
    item_attributes = {"brand": "Pizza Express", "brand_wikidata": "Q662845"}
    start_urls = [
        "https://www.pizzaexpress.com/api/restaurants/FindRestaurantsByLatLong?limit=2000"
    ]

    def parse(self, response):
        for i in response.json():
            item = DictParser.parse(i)

            item["ref"] = i["restaurantId"]
            item["addr_full"] = i["fullAddress"]
            item["postcode"] = i["Postcode"]
            item["street_address"] = clean_address(
                [
                    i["Address1"],
                    i["Address2"],
                    i["Address3"],
                ],
            )

            if i["Location"] == "":
                item["city"] = i["fullAddress"].split(", ")[-2]
            else:
                item["city"] = i["Location"]

            if item["city"] == "Jersey":
                item["country"] = "JE"
            else:
                item["country"] = "GB"

            if img := i.get("image"):
                if img.get("MediaExists"):
                    item["image"] = "https://www.pizzaexpress.com" + img["Src"]

            item["website"] = "https://www.pizzaexpress.com" + i["link"]

            yield item
