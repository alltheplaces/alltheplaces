from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PetParadiseSpider(Spider):
    name = "pet_paradise"
    item_attributes = {"brand": "Pet Paradise", "brand_wikidata": "Q122955413"}
    allowed_domains = ["petparadise.com"]
    start_urls = ("https://www.petparadise.com/locations",)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="pp-loclist__list"]/li'):
            item = Feature()
            item["name"] = self.item_attributes["brand"]
            item["branch"] = location.xpath(".//@data-name").get()
            item["city"] = location.xpath(".//@data-city").get()
            item["state"] = location.xpath(".//@data-state").get()
            item["postcode"] = location.xpath(".//@data-zip").get()
            item["lat"] = location.xpath(".//@data-lat").get()
            item["lon"] = location.xpath(".//@data-lng").get()
            item["addr_full"] = location.xpath(".//@data-address").get()
            item["phone"] = location.xpath(".//@data-phone").get()
            item["email"] = location.xpath(".//@data-email").get()
            item["ref"] = location.xpath(".//@data-i").get()
            item["website"] = response.urljoin(location.xpath('.//*[@class="pp-loclist__view"]/@href').get())
            apply_category(Categories.ANIMAL_BOARDING, item)
            yield item
