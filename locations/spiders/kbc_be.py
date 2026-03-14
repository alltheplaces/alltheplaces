from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations


class KbcBESpider(Spider):
    name = "kbc_be"
    item_attributes = {"brand": "KBC", "brand_wikidata": "Q941020"}

    CASHPOINT_BRAND = {"brand": "Cash", "brand_wikidata": "Q112875867"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("BE"):
            yield JsonRequest(
                url=f'https://www.kbc.be/X9Y-P/elasticsearch-service/api/v3/branches/search?q={city["name"]}&filter=KBC_PALO&filter=CBC_PALO&filter=KBC_VERZ&filter=CBC_VERZ&filter=KBC_AUTO&filter=CBC_AUTO&filter=BATOPIN_AUTO&language=en&radius=10',
                callback=self.parse,
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if data := response.json():
            for bank in data["branches"]:
                item = DictParser.parse(bank)
                item["ref"] = bank["branchId"]
                if "atmType" in bank.keys():
                    apply_category(Categories.ATM, item)
                else:
                    apply_category(Categories.BANK, item)
                    apply_yes_no(Extras.ATM, item, "KBC_AUTO" in bank["branchTypes"])
                    apply_yes_no(Extras.CASH_IN, item, "KBC_AUTO_CASH_IN" in bank["branchTypes"])

                if bank["branchType"] == "BATOPIN_AUTO":
                    item.update(self.CASHPOINT_BRAND)

                yield item
