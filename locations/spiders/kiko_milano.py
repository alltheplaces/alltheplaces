from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class KikoMilanoSpider(JSONBlobSpider):
    name = "kiko_milano"
    item_attributes = {"brand": "KIKO Milano", "brand_wikidata": "Q3812045"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.retailtune.com/storelocator/v1/stores/get",
            data={"language": "en"},
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer 0WNG4nqY725RhWGuaIjlPq8T2NnPxcRwNr1I1Oe4C6pJrrHomfslKXzLpgZKT02y6W0yKnc2SC4",
                "Origin": "https://kiko-stores.kikocosmetics.com",
                "Referer": "https://kiko-stores.kikocosmetics.com/",
            },
        )

    def post_process_item(self, item, response, location):
        item["opening_hours"] = OpeningHours()
        for i in range(len(location["openingHours"])):
            split_hours = location["openingHours"][i].split(",")
            for hours in split_hours:
                hour = hours.split("-")
                if(len(hour) == 2):
                    item["opening_hours"].add_range(DAYS[i], hour[0].replace(" ",""), hour[1].replace(" ",""))
        yield item
