from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

SUPABASE_URL = "https://psrhhuiayrosjnvcfjjv.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBzcmhodWlheXJvc2pudmNmamp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDE3Njg5NTIsImV4cCI6MjAxNzM0NDk1Mn0."
    "nAZoAR_EK6-G5QT24T549h0ftINkKuMqQnoaZHv97Bg"
)


class LegendsBarbersSpider(Spider):
    name = "legends_barbers"
    item_attributes = {
        "brand": "Legends Barber",
        "brand_wikidata": "Q116895407",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"{SUPABASE_URL}/rest/v1/stores?select=*&status=eq.active",
            headers={"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {SUPABASE_ANON_KEY}"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = str(location["id"])
            item["branch"] = item.pop("name", None)
            item["phone"] = None
            if coords := location.get("coordinates"):
                lat, _, lon = coords.partition(",")
                item["lat"] = lat.strip()
                item["lon"] = lon.strip()
            apply_category(Categories.SHOP_HAIRDRESSER, item)
            yield item
