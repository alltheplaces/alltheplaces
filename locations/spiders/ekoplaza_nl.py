import scrapy

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class EkoplazaNLSpider(scrapy.Spider):
    name = "ekoplaza_nl"
    item_attributes = {"brand": "EkoPlaza", "brand_wikidata": "Q47017915"}
    start_urls = [
        "https://www.ekoplaza.nl/api/aspos/stores?distanceFromLatitude=48.8619029&distanceFromLongitude=2.3730383&limit=3000&storeTags=Webshop",
    ]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "*/*"}}

    def parse(self, response):
        for store in response.json().get("Stores"):
            coordinates = store.get("Location")
            oh = OpeningHours()
            for ohs in store.get("OpeningTimes").get("Weekdays"):
                if not ohs.get("OpeningTime") or not ohs.get("ClosingTime"):
                    continue
                day, opens, closes = (
                    sanitise_day(ohs.get("Day")),
                    ohs.get("OpeningTime").lstrip("PT"),
                    ohs.get("ClosingTime").lstrip("PT"),
                )
                opens = opens if "M" in opens else opens + "00M"
                closes = closes if "M" in closes else closes + "00M"
                if opens == closes:
                    continue
                oh.add_range(
                    day=sanitise_day(day),
                    open_time=opens,
                    close_time=closes,
                    time_format="%Hh%Mm",
                )

            props = {
                "ref": store.get("BranchNumber"),
                "name": store.get("Name"),
                "housenumber": store.get("streetNumber"),
                "street": store.get("Street"),
                "country": store.get("CountryCode"),
                "phone": store.get("PhoneNumber"),
                "email": store.get("Email"),
                "postcode": store.get("PostalCode"),
                "city": store.get("City"),
                "lat": coordinates.get("Latitude"),
                "lon": coordinates.get("Longitude"),
                "opening_hours": oh,
            }
            if store.get("FormulaCode") == "EWA":
                props["brand"] = "Bio Drôme Goes"
            yield Feature(**props)
