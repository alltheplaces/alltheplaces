from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class FranprixFRSpider(Spider):
    name = "franprix_fr"
    item_attributes = {"brand": "Franprix", "brand_wikidata": "Q2420096"}
    start_urls = ["https://www.franprix.fr/xhr-cache/resource/stores"]
    requires_proxy = True

    def parse(self, response):
        data = response.json()
        store_data = data.get("list")

        for store in store_data:
            oh = OpeningHours()
            for day in store.get("hours"):
                day_str = day.get("day").title()[:2]
                opening_hours = list(day.get("hours"))
                if not opening_hours:
                    continue
                formatted_hours = opening_hours[0].lstrip("T").split("/")
                oh.add_range(
                    day=day_str,
                    open_time=formatted_hours[0],
                    close_time=formatted_hours[1],
                    time_format="%H:%M",
                )
            properties = {
                "ref": store.get("id"),
                "branch": store.get("store_name"),
                "addr_full": store.get("street"),
                "city": store.get("city"),
                "phone": store.get("phone"),
                "postcode": store.get("postcode"),
                "lat": store.get("lat"),
                "lon": store.get("lon"),
                "website": f"https://www.franprix.fr/magasins/{store.get('id')}",
                "opening_hours": oh.as_opening_hours(),
            }
            yield Feature(**properties)
