import scrapy

from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import GeojsonPointItem

TIME_FORMAT = "%H:%M %p"


class LidsSpider(scrapy.Spider):
    name = "lids"
    item_attributes = {"brand": "Lids", "brand_wikidata": "Q19841609"}
    allowed_domains = ["lids.com"]
    custom_settings = {
        "COOKIES_ENABLED": True,
        "USER_AGENT": " Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    }

    def start_requests(self):
        url = "https://www.lids.com/api/data/v2/stores/514599?lat=30.2729209&long=-97.74438630000002&num=12000&shipToStore=false"
        headers = {"Accept": "application/json", "Host": "www.lids.com"}
        yield scrapy.Request(url, method="GET", headers=headers)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for day in DAYS_FULL:
            opening_hours.add_range(
                day=DAYS_EN[day],
                open_time=hours[day.lower() + "Open"],
                close_time=hours[day.lower() + "Closed"],
                time_format=TIME_FORMAT,
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        ldata = response.json()

        for row in ldata:
            properties = {
                "ref": row["storeId"],
                "name": row["name"],
                "street_address": row["address"]["addressLine1"],
                "city": row["address"]["city"],
                "postcode": row["address"]["zip"],
                "state": row["address"]["state"],
                "country": row["address"]["country"],
                "lat": row["location"]["coordinate"]["latitude"],
                "lon": row["location"]["coordinate"]["longitude"],
                "phone": row["phone"],
                "website": "https://www.lids.com" + row["taggedUrl"],
            }

            hours = self.parse_hours(row)

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
