from datetime import datetime
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import set_closed

QUERY = """
query($limit: Int!, $offset: Int!) {
  facilities(first: $limit, skip: $offset) {
    total
    results {
      id
      slug
      location { address zip city country geo { lat lon } }
      markets {
        id
        type
        name
        phone
        email
        opening_date
        closing_date
        opening_hours {
          active
          opening_hours {
            day_of_week
            time_open1
            time_close1
            time_open2
            time_close2
            on_request1
            on_request2
          }
        }
      }
    }
  }
}
"""


class MigrosCHSpider(Spider):
    name = "migros_ch"
    brands = {
        "chng": ("Migros Change", "Q115659823", Categories.BUREAU_DE_CHANGE),
        "cof": ("Migros Café", "Q115661379", Categories.COFFEE_SHOP),
        "flori": ("Florissimo", "Q115659418", Categories.SHOP_FLORIST),
        "gour": ("Migros Take Away", "Q111826610", Categories.FAST_FOOD),
        "mno": ("Migrolino", "Q56745088", Categories.SHOP_CONVENIENCE),
        "mp": ("Migros Partner", "Q115661515", Categories.SHOP_SUPERMARKET),
        "out": ("Outlet Migros", "Q115659564", Categories.SHOP_SUPERMARKET),
        "pickmup": ("PickMup Box", "Q115679275", Categories.PRODUCT_PICKUP),
        "res": ("Migros Restaurant", "Q111803848", Categories.RESTAURANT),
        "super": ("Migros", "Q680727", Categories.SHOP_SUPERMARKET),
        "voi": ("VOI", "Q110277616", Categories.SHOP_SUPERMARKET),
    }
    api_url = "https://api.migros.ch/migros/sales/branches/v1/graphql"
    api_key = "c3C2RemDDaYV8b2NPDev1MEDn12KsonY"
    page_size = 200

    async def start(self):
        yield self.api_request(0)

    def api_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url=self.api_url,
            data={"query": QUERY, "variables": {"limit": self.page_size, "offset": offset}},
            headers={"x-api-key": self.api_key, "Accept-Language": "de"},
            cb_kwargs={"offset": offset},
        )

    def parse(self, response: Response, offset: int, **kwargs: Any) -> Any:
        facilities = response.json()["data"]["facilities"]
        for facility in facilities["results"]:
            yield from self.parse_facility(facility)
        if offset + self.page_size < facilities["total"]:
            yield self.api_request(offset + self.page_size)

    def parse_facility(self, facility: dict) -> Any:
        for market in facility["markets"]:
            brand_key = market["type"].split("_")[0]
            if brand_key not in self.brands:
                continue
            brand, brand_wikidata, category = self.brands[brand_key]
            market.update(facility["location"])
            if geo := market.pop("geo", None):
                market.update(geo)

            item = DictParser.parse(market)
            item["brand"] = brand
            item["brand_wikidata"] = brand_wikidata
            item["name"] = brand
            item["street_address"] = item.pop("addr_full", None)
            item["opening_hours"] = self.parse_opening_hours(market)

            if start_date := market.get("opening_date"):
                item["extras"]["start_date"] = datetime.fromisoformat(start_date).strftime("%Y-%m-%d")
            if end_date := market.get("closing_date"):
                set_closed(item, datetime.fromisoformat(end_date))

            apply_category(category, item)
            yield item

    @staticmethod
    def parse_opening_hours(market: dict) -> Any:
        if market["type"] == "pickmup_247pmubox":
            return "24/7"
        oh = OpeningHours()
        for block in market.get("opening_hours") or []:
            if not block.get("active"):
                continue
            for hours in block.get("opening_hours") or []:
                day = DAYS[hours["day_of_week"] - 1]
                ranges = [
                    (hours.get("time_open1"), hours.get("time_close1")),
                    (hours.get("time_open2"), hours.get("time_close2")),
                ]
                opened = False
                for open_time, close_time in ranges:
                    if open_time and close_time:
                        oh.add_range(day, open_time, close_time)
                        opened = True
                if not opened and not hours.get("on_request1") and not hours.get("on_request2"):
                    oh.set_closed(day)
        return oh
