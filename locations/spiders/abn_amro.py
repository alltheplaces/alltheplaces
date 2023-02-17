import scrapy

from locations.hours import DAYS_SE, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class AbnAmroNLSpider(scrapy.Spider):
    name = "abn_amro_nl"
    item_attributes = {"brand": "ABN AMRO", "brand_wikidata": "Q287471"}
    start_urls = ["https://www.abnamro.nl/servicelocations/v3/"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response, **kwargs):
        for stores in response.json().get("serviceLocations"):
            store = stores.get("serviceLocation")
            oh = OpeningHours()
            for services in store.get("services"):
                for day, hours in services.get("officeHours").items():
                    if "-" not in hours[0]:
                        continue
                    starting, closing = hours[0].split("-")
                    oh.add_range(day, starting, closing)
            yield Feature(
                {
                    "ref": store.get("propRef"),
                    "name": store.get("owner"),
                    "street_address": store.get("address"),
                    "postcode": store.get("zipCode"),
                    "city": store.get("city"),
                    "lat": store.get("lat"),
                    "lon": store.get("lng"),
                    "opening_hours": oh,
                    "extras": {"store_type": store.get("locationType")},
                }
            )
