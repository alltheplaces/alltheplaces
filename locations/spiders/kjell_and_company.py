from datetime import datetime
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

COUNTRIES = {"NOR": "NO", "SWE": "SE"}
REQUEST_BODY = '[{t:"Avensia.Common.Store.ChooseStoreListViewModel,Avensia.Common"}]'


class KjellAndCompanySpider(Spider):
    name = "kjell_and_company"
    item_attributes = {"brand": "Kjell & Company", "brand_wikidata": "Q6419332"}
    allowed_domains = ["kjell.com"]

    async def start(self) -> AsyncIterator[Any]:
        for country_code, country in COUNTRIES.items():
            yield JsonRequest(
                url="https://www.kjell.com/resolvedynamicdata",
                data=REQUEST_BODY,
                cookies={"CountryCode": country_code},
                cb_kwargs={"country": country},
                dont_filter=True,
            )

    def parse(self, response, country):
        for component in response.json():
            for location in component.get("stores", []):
                item = DictParser.parse(location)
                item["country"] = country
                item["opening_hours"] = self.parse_hours(location)
                item["branch"] = item.pop("name")
                apply_yes_no(PaymentMethods.CASH, item, not location.get("noCash", False))
                apply_category(Categories.SHOP_ELECTRONICS, item)
                yield item

    @staticmethod
    def parse_hours(location: dict) -> OpeningHours | None:
        if not (hours_data := location.get("openHours")):
            return None
        oh = OpeningHours()
        for entry in hours_data:
            day = DAYS[datetime.strptime(f'{entry["date"]}/{entry["year"]}', "%d/%m/%Y").weekday()]
            if entry.get("isClosed"):
                oh.set_closed(day)
            else:
                oh.add_range(day, entry.get("open"), entry.get("close"))
        return oh
