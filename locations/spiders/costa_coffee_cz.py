import scrapy

from locations.categories import Categories
from locations.items import Feature


class CostaCoffeeCZSpider(scrapy.Spider):
    name = "costa_coffee_cz"
    brands = {
        "costa": {"brand": "Costa Coffee", "brand_wikidata": "Q608845", "extras": Categories.COFFEE_SHOP.value},
        "express": {
            "brand": "Costa Express",
            "brand_wikidata": "Q113556385",
            "extras": Categories.VENDING_MACHINE_COFFEE.value,
        },
    }
    SHELL = {"brand": "Shell", "brand_wikidata": "Q154950"}
    start_urls = ["https://loc.costa-coffee.cz/locator/"]

    def parse(self, response, **kwargs):
        for shop in response.xpath("//*[@data-lat]"):
            item = Feature()
            item["ref"] = shop.xpath("./@data-id").get()
            item["name"] = shop.xpath("./@data-name").get()
            item["lat"] = shop.xpath("./@data-lat").get()
            item["lon"] = shop.xpath("./@data-lng").get()
            item["city"] = shop.xpath("./@data-city").get()
            item["postcode"] = shop.xpath("./@data-postal_code").get()
            item["street_address"] = shop.xpath("./@data-address").get()
            item["addr_full"] = shop.xpath('.//*[@class="result-address"]//text()').get()
            item["website"] = response.url
            store_type = shop.xpath("./@data-type").get()
            if brand := self.brands.get(store_type):
                item.update(brand)
            if "SHELL" in item["name"].upper():
                item["located_in"], item["located_in_wikidata"] = self.SHELL.values()
            yield item
