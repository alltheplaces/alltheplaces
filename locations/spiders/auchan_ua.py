from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class AuchanUASpider(PlaywrightSpider):
    name = "auchan_ua"
    item_attributes = {"brand_wikidata": "Q4073419"}
    custom_settings = {"ROBOTSTXT_OBEY": False} | DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://auchan.ua/graphql",
            data={
                "query": """
                    query getWarehouses {
                        getAuchanWarehouses {
                            warehouses {
                                code
                                city: city_ua
                                city_ru
                                hours
                                address
                                title
                                position {
                                    latitude
                                    longitude
                                }
                            }
                        }
                    }
                """,
                "operationName": "getWarehouses",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["getAuchanWarehouses"]["warehouses"]:
            store.update(store.pop("position"))
            item = DictParser.parse(store)
            item["branch"] = (
                item.pop("name").removeprefix("Мой Auchan ").removeprefix("Auchan ").removeprefix("Pick Up Point ")
            )
            item["street_address"] = item.pop("addr_full")
            item["extras"]["city:ru"] = store["city_ru"]
            item["extras"]["city:uk"] = store["city"]
            item["ref"] = store["code"]
            item["opening_hours"] = OpeningHours()
            if store["hours"] not in ["Зачинено", "Зачинений"]:
                open_time, close_time = store["hours"].split("-")
                for day in DAYS:
                    item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
