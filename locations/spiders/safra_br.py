from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SafraBRSpider(scrapy.Spider):
    name = "safra_br"
    item_attributes = {"brand": "Banco Safra", "brand_wikidata": "Q4116096"}
    start_urls = ["https://www.safra.com.br/lumis/api/rest/agencies/lumgetdata/listAgencies"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.json()["rows"]:
            item = DictParser.parse(bank)
            item["branch"] = item.pop("name")
            item["street_address"] = bank["adress"]
            item["postcode"] = bank["cep"]
            apply_category(Categories.BANK, item)
            yield item
