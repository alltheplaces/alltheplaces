import scrapy
from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours

from locations.items import Feature


class PostaSpider(scrapy.Spider):
    name = "posta_si"
    item_attributes = {"brand": "Pošta Slovenije", "brand_wikidata": "Q6522631"}
    allowed_domains = ["www.posta.si"]

    custom_settings = {"ROBOTSTXT_OBEY": False}

    start_urls = [
        "https://www.posta.si/_vti_bin/PostaSI/PostOffices/PostOfficesService.svc/SearchPostOffices/" + c + "/"
        for c in "abcčdefghijklmnoprsštuvzž"
    ]

    ids_seen = set()

    def parse(self, response):
        for posta in response.json():
            if posta["PostOfficeId"] in self.ids_seen:
                continue
            self.ids_seen.add(posta["PostOfficeId"])

            feature = Feature(
                ref=posta["PostOfficeId"],
                name=posta.get("Title"),
                lat=posta["Geo"]["Lat"],
                lon=posta["Geo"]["Lng"],
                street_address=posta["Address"],
                country="SI",
                phone=posta.get("FirstPhone"),
                opening_hours=self.parse_open_hours(posta["WorkTimes"] or {}),
            )

            apply_category(Categories.POST_OFFICE, feature)

            services = [service["ServiceId"] for service in posta["Services"]]

            apply_yes_no("sells:lottery", feature, 8 in services)
            apply_yes_no("services:copy", feature, 9 in services)

            if 2 in services:
                apply_category(Categories.BUREAU_DE_CHANGE, feature)

            yield feature

    def parse_open_hours(self, obj):
        opening_hours = OpeningHours()

        for day in DAYS_FULL:
            times = obj.get(day + "WorkTime")
            if not times:
                continue
            if times["From1"]:
                opening_hours.add_range(day=day[:2], open_time=times["From1"], close_time=times["To1"])
            if times["From2"]:
                opening_hours.add_range(day=day[:2], open_time=times["From2"], close_time=times["To2"])

        return opening_hours.as_opening_hours()
