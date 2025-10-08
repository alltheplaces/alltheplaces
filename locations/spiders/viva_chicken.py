import scrapy

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class VivaChickenSpider(scrapy.Spider):
    name = "viva_chicken"
    item_attributes = {"brand": "Viva Chicken"}
    allowed_domains = ["www.vivachicken.com"]
    start_urls = ["https://www.vivachicken.com/locations"]

    def parse(self, response):
        for restaurant in response.xpath('//*[@class="locations_grid__locations_list"]//li'):
            item = Feature()
            item["name"] = self.item_attributes["brand"]
            item["branch"] = restaurant.xpath(".//h2//text()").get()
            item["street_address"] = restaurant.xpath('.//*[@class="locations_grid__address"]//text()').get()
            item["addr_full"] = ",".join(
                [item["street_address"], restaurant.xpath('.//*[@class="locations_grid__address"]//text()[2]').get()]
            )
            item["phone"] = restaurant.xpath('.//*[contains(@href,"tel:")]/text()').get().replace("Phone: ", "")
            item["ref"] = item["website"] = restaurant.xpath('.//*[@class="locations_grid__title_url"]/@href').get()
            extract_google_position(item, restaurant)
            apply_category(Categories.RESTAURANT, item)
            yield item
