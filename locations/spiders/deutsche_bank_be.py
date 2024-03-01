import scrapy

from locations.categories import Categories
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class DeutscheBankBESpider(scrapy.Spider):
    name = "deutsche_bank_be"
    start_urls = ["https://public.deutschebank.be/f2w/data/agencies.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = {"brand": "Deutsche Bank", "brand_wikidata": "Q66048"}

    def parse(self, response, **kwargs):
        for store in response.json().get("agencies"):
            oh = OpeningHours()
            for i, week in enumerate(store.get("rangeHours")):
                for day in week:
                    for hour in day:
                        opening_time, closing_time = hour.split(" - ")
                        oh.add_range(day=DAYS[i], open_time=opening_time, close_time=closing_time)
            website = store.get("webpage", {})
            street_address = store.get("address").get("fr").replace("<br />", ",")
            phone = store.get("phone").get("fr")

            yield Feature(
                {
                    "ref": store.get("branchId"),
                    "name": store.get("id"),
                    "addr_full": street_address,
                    "phone": phone,
                    "website": website.get("fr"),
                    "lat": store.get("lat"),
                    "lon": store.get("long"),
                    "opening_hours": oh.as_opening_hours(),
                    "extras": Categories.BANK.value,
                }
            )
