from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class FraserGBSpider(Spider):
    name = "fraser_gb"
    item_attributes = {"brand": "House of Fraser", "brand_wikidata": "Q5928422"}
    start_urls = [
        "https://www.houseoffraser.co.uk/stores/search?countryName=United%20Kingdom&countryCode=GB&lat=0&long=0&sd=40"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="StoreFinderStore"]'):
            item = Feature()
            item["ref"] = location.xpath("@data-store-code").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["website"] = response.urljoin(location.xpath(".//a/@href").get())

            name = location.xpath(".//span/text()").get()
            if name.startswith("Frasers"):
                item["name"] = "Frasers"
            else:
                item["name"] = "House of Fraser"
            item["branch"] = name.removeprefix("Frasers ").removeprefix("House of Fraser ").removesuffix(" FRA")

            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            yield item
