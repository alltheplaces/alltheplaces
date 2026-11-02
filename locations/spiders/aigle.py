import re
from typing import AsyncIterator, Iterable

from scrapy import Request, Selector, Spider
from scrapy.http import TextResponse

from locations.categories import apply_yes_no
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class AigleSpider(Spider):
    name = "aigle"
    item_attributes = {"brand_wikidata": "Q404391"}

    async def start(self) -> AsyncIterator[Request]:
        # The other Aigle sites (BE, UK, EU) list no stores or the same French ones.
        yield Request(
            "https://www.aigle.com/on/demandware.store/Sites-aigle-fr-Site/fr_FR/Stores-InitMarkersMap",
            method="POST",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for store in response.json():
            name = store["storename"]
            # Department store corners such as Galeries Lafayette Bordeaux.
            if not re.match(r"(Boutique|Outlet) Aigle ", name):
                continue
            info = Selector(text=store["htmlInfoStore"])
            item = Feature()
            item["ref"] = store["id"]
            item["branch"] = name.split(" Aigle ", 1)[1]
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["street_address"] = info.css(".CC-store-street::text").get()
            item["postcode"], item["city"] = (info.css(".CC-store-city::text").get() or "").split("\xa0", 1)
            item["postcode"] = item["postcode"].replace(" ", "")
            item["phone"] = (info.css(".CC-store-telephone::text").get() or "").removeprefix("Tél:")
            item["website"] = (
                f"https://www.aigle.com/on/demandware.store/Sites-aigle-fr-Site/fr_FR/Stores-ShowDetails?id={store['id']}"
            )

            if name.startswith("Outlet "):
                item["name"] = "Aigle Outlet"
                apply_yes_no("factory_outlet", item, True)

            item["opening_hours"] = OpeningHours()
            for row in info.css(".CC-schedule-info-map tr"):
                day, hours = row.css("td::text").getall()[:2]
                if not (day := sanitise_day(day, DAYS_FR)):
                    continue
                if "Fermé" in hours:
                    item["opening_hours"].set_closed(day)
                    continue
                # Lunch breaks read like "10:00-12:30 - 14:00-19:00".
                times = re.findall(r"\d{1,2}:\d{2}", hours)
                for open_time, close_time in zip(times[::2], times[1::2]):
                    item["opening_hours"].add_range(day, open_time, close_time)

            yield item
