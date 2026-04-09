import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BancoDaAmazoniaBRSpider(Spider):
    name = "banco_da_amazonia_br"
    item_attributes = {"brand": "Banco da Amazônia", "brand_wikidata": "Q16496429"}
    start_urls = ["https://www.bancoamazonia.com.br/o-banco/nossas-agencias"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = response.xpath('//*[contains(text(),"agencies")]//text()').get().replace("\\", "")
        for location in json.loads(re.search(r"agencies\":(\[.+\]),", raw_data).group(1)):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.BANK, item)
            yield item
