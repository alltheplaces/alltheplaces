from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.items import Feature


class LOccitaneAuBresilBRSpider(Spider):
    name = "l_occitane_au_bresil_br"
    item_attributes = {"brand": "L'Occitane", "brand_wikidata": "Q1880676"}
    url_template = "https://br.loccitaneaubresil.com/on/demandware.store/Sites-LoccitaneBR-Site/pt_BR/Stores-FindStores?showMap=true&radius=300&cityName={}"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        for city in city_locations("BR", 100_000):
            yield Request(self.url_template.format(city["name"]), callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["addr_full"] = item.pop("street_address")
            apply_category(Categories.SHOP_COSMETICS, item)
            yield item
