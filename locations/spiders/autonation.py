import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AutoNationSpider(scrapy.Spider):
    name = "auto_nation"
    allowed_domains = ["autonation.com"]
    item_attributes = {"brand": "Auto Nation", "brand_wikidata": "Q784804"}
    start_urls = [
        "https://www.autonation.com/StoreDetails/Get/?lat=30.218908309936523&long=-97.8546142578125&radius=5000&zipcode=78749"
    ]
    requires_proxy = True

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            try:
                day = DAYS[hour["Day"]]
                open_time = hour["StartTime"]
                if len(open_time) == 7:
                    open_time = open_time.rjust(8, "0")
                close_time = hour["EndTime"]
                if len(close_time) == 7:
                    close_time = close_time.rjust(8, "0")
                if open_time == "":
                    continue
            except:
                continue

            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores["Store"]:
            properties = {
                "ref": store["StoreId"],
                "name": store["Name"],
                "street_address": merge_address_lines([store["AddressLine1"], store["AddressLine2"]]),
                "city": store["City"],
                "state": store["StateCode"],
                "postcode": store["PostalCode"],
                "country": "US",
                "lat": store["Latitude"],
                "lon": store["Longitude"],
                "phone": store["Phone"],
                "website": "https://www.autonation.com/dealers/" + store["StoreDetailsUrl"],
                "extras": {"sells": store["Makes"]},
            }

            hours = self.parse_hours(store["StoreDetailedHours"])

            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
