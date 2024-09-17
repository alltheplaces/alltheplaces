from datetime import datetime

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class BobEvansUSSpider(SitemapSpider):
    name = "bob_evans_us"
    item_attributes = {"brand": "Bob Evans", "brand_wikidata": "Q4932386"}
    sitemap_urls = [
        "https://www.bobevans.com/sitemap.xml",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def sitemap_filter(self, entries):
        for entry in entries:
            if "/locations/" in entry["loc"]:
                slug = entry["loc"].rsplit("/", 1)[-1]
                entry["loc"] = f"https://www.bobevans.com/api/location/details/{slug}"
                yield entry

    def parse(self, response):
        data = response.json()
        item = DictParser.parse(data)
        item["website"] = f'https://www.bobevans.com/locations/{data["slug"]}'
        item["opening_hours"] = self.parse_hours(data["businessHours"])
        item.pop("name", None)
        yield item

    @staticmethod
    def parse_hours(hours):
        # The opening hours are specified on a day-by-day basis.
        # (In ISO format, as local time with UTC offset)
        # Optimistically take the union of all given opening hours on the
        # assumption that holiday hours will be strictly less than regular
        # hours.
        oh = OpeningHours()
        for row in hours:
            start = datetime.fromisoformat(row["startDate"])
            end = datetime.fromisoformat(row["endDate"])
            day = DAYS[start.weekday()]
            start_time = start.strftime("%H:%M")
            end_time = end.strftime("%H:%M")
            oh.add_range(day, start_time, end_time)
        return oh.as_opening_hours()
