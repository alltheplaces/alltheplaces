# -*- coding: utf-8 -*-
import scrapy
import datetime
import json


from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "fridayHours": "Fr",
    "mondayHours": "Mo",
    "saturdayHours": "Sa",
    "sundayHours": "Su",
    "thursdayHours": "Th",
    "tuesdayHours": "Tu",
    "wednesdayHours": "We",
}


class SephoraSpider(scrapy.Spider):
    name = "sephora"
    item_attributes = {"brand": "Sephora"}
    allowed_domains = ["www.sephora.com"]
    download_delay = 0.2
    start_urls = ("https://www.sephora.com/storelist",)

    def store_hours(self, response):
        opening_hours = OpeningHours()
        weekdays = response

        for day, hrs in weekdays.items():
            if "closedDays" in day or "textColor" in day or "timeZone" in day:
                continue
            elif "CLOSED" in hrs:
                continue
            else:
                try:
                    open, close = hrs.split("-")
                    open = open.strip()
                    close = close.strip()
                    if ":" in open:
                        open_time = datetime.datetime.strptime(
                            open, "%I:%M%p"
                        ).strftime("%H:%M")
                    else:
                        open_time = datetime.datetime.strptime(open, "%I%p").strftime(
                            "%H:%M"
                        )

                    if ":" in close:
                        close_time = datetime.datetime.strptime(
                            close, "%I:%M%p"
                        ).strftime("%H:%M")
                    else:
                        close_time = datetime.datetime.strptime(close, "%I%p").strftime(
                            "%H:%M"
                        )
                except ValueError:
                    continue
                opening_hours.add_range(
                    DAY_MAPPING[day],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath('//a[@class="css-j9u336 "]/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        jsondata = json.loads(
            response.xpath('//script[@id="linkJSON"]/text()').extract_first()
        )
        data = jsondata[2]["props"]
        properties = {
            "website": response.urljoin(data["storeInfo"]["seoCanonicalUrl"]),
            "ref": data["storeInfo"]["storeId"],
            "name": data["storeInfo"]["displayName"],
            "phone": data["storeInfo"]["address"]["phone"],
            "addr_full": data["storeInfo"]["address"]["address1"],
            "city": data["storeInfo"]["address"]["city"],
            "state": data["storeInfo"]["address"]["state"],
            "postcode": data["storeInfo"]["address"]["postalCode"],
            "country": data["storeInfo"]["address"]["country"],
            "lon": float(data["storeInfo"]["longitude"]),
            "lat": float(data["storeInfo"]["latitude"]),
        }
        opening_hours = self.store_hours(data["storeInfo"]["storeHours"])

        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)
