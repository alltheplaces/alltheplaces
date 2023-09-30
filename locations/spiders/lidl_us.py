import scrapy

from locations.items import Feature
from locations.spiders.lidl_gb import LidlGBSpider


class LidlUSSpider(scrapy.Spider):
    name = "lidl_us"
    item_attributes = LidlGBSpider.item_attributes
    allowed_domains = ["lidl.com"]
    start_urls = [
        "https://mobileapi.lidl.com/v1/stores",
    ]

    def parse(self, response):
        data = response.json()

        for store in data["results"]:
            properties = {
                "name": store["name"],
                "ref": store["crmStoreID"],
                "street_address": store["address"]["street"],
                "city": store["address"]["city"],
                "state": store["address"]["state"],
                "postcode": store["address"]["zip"],
                "country": store["address"]["country"],
                "phone": store["phone"],
                "lat": float(store["coordinates"]["lat"]),
                "lon": float(store["coordinates"]["lon"]),
            }

            yield Feature(**properties)
