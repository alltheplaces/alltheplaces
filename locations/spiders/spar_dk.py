from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES

DAYS = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    0: "Sunday",
}


class SparDKSpider(Spider):
    name = "spar_dk"
    item_attributes = SPAR_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            "https://spar.dk/search",
            data={
                "params": {"wt": "json"},
                "filter": [],
                "query": 'ss_search_api_datasource:"entity:node" AND bs_status:true AND ' 'ss_type:"store"',
                "limit": 1000,
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["docs"]:
            opening_hours = OpeningHours()
            try:
                for entry in eval(
                    location["sm_solr_opening_hours"][0].replace("false", "False").replace("true", "True")
                ):
                    if not entry["all_day"]:
                        day = DAYS[entry["day"]]
                        open_time = str(entry["starthours"])
                        close_time = str(entry["endhours"])
                        opening_hours.add_range(day, open_time, close_time, time_format="%H%M")
            except NameError:
                pass
            properties = {
                "branch": location["tm_X3b_en_title"][0].removeprefix("SPAR "),
                "ref": location["id"],
                "street_address": location["tm_X3b_en_address_line1"][0],
                "city": location["tm_X3b_en_locality"][0],
                "opening_hours": opening_hours.as_opening_hours(),
                "postcode": location["tm_X3b_en_postal_code"][0],
                "phone": location["ss_field_store_phone"],
                "lat": location["fts_lat"],
                "lon": location["fts_lon"],
                "website": location.get("ss_field_custom_pane_link"),
            }

            apply_category(Categories.SHOP_SUPERMARKET, properties)

            yield Feature(**properties)
