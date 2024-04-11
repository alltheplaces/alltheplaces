import scrapy
from scrapy.http import JsonRequest
from scrapy.selector import Selector

from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.kfc import KFC_SHARED_ATTRIBUTES


class KFCSGSpider(scrapy.Spider):
    name = "kfc_sg"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["www.kfc.com.sg"]
    start_urls = ["https://www.kfc.com.sg/Location/Search"]

    def parse(self, response):
        restaurant_ids = response.xpath('//div[contains(@class, "restaurantDetails")]/@data-restaurantid').getall()
        for restaurant_id in restaurant_ids:
            data = {
                "DeliveryAddressInformation": {
                    "City": "",
                    "StateCode": "",
                    "State": "",
                    "Comments": "",
                },
                "RestaurantSearchKeyword": "",
                "OrderReadyDateTime": "",
                "SearchedLocationGeoCode": {
                    "DeliveryAddress": {
                        "City": "",
                        "StateCode": "",
                        "Comments": "",
                    },
                    "Latitude": None,
                    "Longitude": None,
                },
                "SelectedRestaurantId": restaurant_id,
                "topOneStore": False,
                "IsAllKFC": False,
                "isShowOrderButton": True,
            }
            yield JsonRequest(
                url="https://www.kfc.com.sg/KFCLocation/StoreDetails",
                method="POST",
                data=data,
                meta={"restaurant_id": restaurant_id},
                callback=self.parse_store,
            )

    def parse_store(self, response):
        data_html = Selector(text=" ".join(response.json()["DataObject"].split()))
        properties = {
            "ref": response.meta["restaurant_id"],
            "name": data_html.xpath('//div[contains(@class, "content")]/h1/text()').get().strip(),
            "lat": data_html.xpath('//input[@id="Latitude"]/@value').get().strip(),
            "lon": data_html.xpath('//input[@id="Longitude"]/@value').get().strip(),
            "addr_full": " ".join(" ".join(data_html.xpath("//address/text()").getall()).split()),
            "phone": data_html.xpath('//a[contains(@href, "tel:")]/text()').get(),
        }
        oh = OpeningHours()
        hours_raw = (
            " ".join(data_html.xpath('//table[contains(@class, "open-hours")]/tbody/tr/td/text()').getall())
            .replace("Closed", "0:00 AM-0:00 AM")
            .replace("-", " ")
            .replace(" AM", "AM")
            .replace(" PM", "PM")
        ).split()
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if day[1] == "0:00AM" and day[2] == "0:00AM":
                continue
            oh.add_range(day[0], day[1], day[2], "%I:%M%p")
        properties["opening_hours"] = oh.as_opening_hours()
        yield Feature(**properties)
