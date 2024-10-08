import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PostaSISpider(scrapy.Spider):
    name = "posta_si"
    item_attributes = {"brand": "Pošta Slovenije", "brand_wikidata": "Q6522631"}
    allowed_domains = ["www.posta.si"]

    custom_settings = {"ROBOTSTXT_OBEY": False}

    # There is no "show all" option, but we can search for every letter to get all of them
    start_urls = [
        "https://www.posta.si/_vti_bin/PostaSI/PostOffices/PostOfficesService.svc/PostalOffice/" + c
        for c in "abcčdefghijklmnoprsštuvzž"
    ]

    ids_seen = set()

    def parse(self, response):
        for posta in response.json():

            # Skip everything that isn't a post office (newsagents, petrol stations...)
            # 0 = Pošta, 1 = BS petrol, 2 = PS Paketomat, 4 = BS MOL, 7 = TRAFIKA 3DVA
            if posta["VrstaEnote"] != 0:
                continue

            # Units with no physical location, only used for administrative purposes
            if "Pin" not in posta:
                continue

            # Skip already-seen post offices
            if posta["PostalId"] in self.ids_seen:
                continue
            self.ids_seen.add(posta["PostalId"])

            feature = Feature(
                ref=posta["PostalId"],
                name=posta["PostalClassNumAndTitle"],
                lat=posta["Pin"]["GPSx"],
                lon=posta["Pin"]["GPSy"],
                street_address=posta["PostalAddress"],
                country="SI",
                phone=posta.get("FirstPhone"),
                opening_hours=self.parse_open_hours(posta["FormatWorkingDays"]),
            )

            apply_category(Categories.POST_OFFICE, feature)

            # Some post offices offer additional services. Descriptions are next to the IDs in the JSON reposne ("ServiceTitle")
            service_ids = [service["PostalServiceId"] for service in posta["PostalOfficeServices"]]
            apply_yes_no("sells:lottery", feature, 11 in service_ids)  # 11 = Igre na srečo Loterije Slovenije
            apply_yes_no("services:copy", feature, 12 in service_ids)  # 12 = Fotokopiranje

            yield feature

    def parse_open_hours(self, lst):
        opening_hours = OpeningHours()

        for times in lst:
            day = DAYS[times["Day"] - 1]

            if times["WorkingTimeFrom"]:
                opening_hours.add_range(day=day, open_time=times["WorkingTimeFrom"], close_time=times["WorkingTimeTo"])
            if times["OtherTimeFrom"]:
                opening_hours.add_range(day=day, open_time=times["OtherTimeFrom"], close_time=times["OtherTimeTo"])

        return opening_hours.as_opening_hours()
