from scrapy import Spider

from locations.categories import Categories
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class EpakaPLSpider(Spider):
    name = "epaka_pl"
    item_attributes = {"brand": "Epaka.pl", "brand_wikidata": "Q123028724", "extras": Categories.POST_OFFICE.value}
    start_urls = ["https://www.epaka.pl/api/getPoints.xml"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for poi in response.xpath("//points/point"):
            opening_hours = OpeningHours()
            for opening_day in poi.xpath("open_hours/day"):
                week_day = opening_day.xpath("day_of_week/text()").get().capitalize()
                open_time = opening_day.xpath("open/text()").get()
                close_time = opening_day.xpath("close/text()").get()

                opening_hours.add_range(
                    day=DAYS_PL.get(week_day), open_time=open_time, close_time=close_time, time_format="%H:%M:%S"
                )

            yield Feature(
                {
                    "ref": poi.xpath("id/text()").get(),
                    "lat": poi.xpath("lat/text()").get(),
                    "lon": poi.xpath("lng/text()").get(),
                    "city": poi.xpath("city/text()").get(),
                    "phone": poi.xpath("telephone/text()").get().split(",", maxsplit=1)[0],
                    "website": poi.xpath("www/text()").get(),
                    "postcode": poi.xpath("post_code/text()").get(),
                    "street": poi.xpath("street/text()").get().strip(),
                    "housenumber": poi.xpath("number/text()").get(),
                    "email": poi.xpath("email/text()").get(),
                    "opening_hours": opening_hours,
                }
            )
