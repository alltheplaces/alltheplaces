import json

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class RainbowShopsSpider(scrapy.Spider):
    name = "rainbow_shops"
    allowed_domains = ["rainbowshops.com"]
    start_urls = [
        "https://stores.rainbowshops.com/umbraco/api/location/GetAllLocations",
    ]
    item_attributes = {"brand": "Rainbow Shops", "brand_wikidata": "Q7284708"}

    def parse(self, response):
        base_url = "https://stores.rainbowshops.com/umbraco/api/Location/GetDataByState?region={region}"

        data = response.xpath("//text()").extract_first()
        states = json.loads(data)

        for state in states:
            region = state["MainAddress.Region"]
            url = base_url.format(region=region)

            yield scrapy.Request(url=url, callback=self.parse_stores)

        ## To get PR
        url = "https://stores.rainbowshops.com/umbraco/api/location/GetDataByCoordinates?longitude=-64.748032&latitude=17.729958&distance=undefined&units=miles"
        yield scrapy.Request(url=url, callback=self.parse_stores)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for day in DAYS:
            open_time = hours[day]["Ranges"][0]["StartTime"]
            close_time = hours[day]["Ranges"][0]["EndTime"]
            if open_time is not None:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        data = response.xpath("//text()").extract_first()
        places = json.loads(data)

        for place in places["StoreLocations"]:
            properties = {
                "ref": place["ExtraData"]["ReferenceCode"],
                "name": place["ExtraData"]["LocationDescriptor"],
                "addr_full": place["ExtraData"]["Address"]["AddressNonStruct_Line1"],
                "city": place["ExtraData"]["Address"]["Locality"],
                "state": place["ExtraData"]["Address"]["Region"],
                "postcode": place["ExtraData"]["Address"]["PostalCode"],
                "country": place["ExtraData"]["Address"]["CountryCode"],
                "lat": place["Location"]["coordinates"][1],
                "lon": place["Location"]["coordinates"][0],
                "phone": place["ExtraData"]["Phone"],
            }

            try:
                hours = self.parse_hours(place["ExtraData"]["HoursOfOpStruct"])
                if hours:
                    properties["opening_hours"] = hours
            except:
                pass

            yield Feature(**properties)
