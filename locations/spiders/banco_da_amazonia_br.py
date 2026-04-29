import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class BancoDaAmazoniaBRSpider(Spider):
    name = "banco_da_amazonia_br"
    item_attributes = {"brand": "Banco da Amazônia", "brand_wikidata": "Q16496429"}
    start_urls = ["https://www.bancoamazonia.com.br/o-banco/nossas-agencias"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = (
            (response.xpath('//*[contains(text(),"agencies")]//text()').get())
            .replace("\\n", "")
            .replace("\\", "")
            .replace('""', '"')
        )
        for location in json.loads(re.search(r"agencies\":(\[.+\]),\"animation", raw_data).group(1)):
            item = DictParser.parse(location)
            item["addr_full"] = clean_address(item["addr_full"].replace("Bairro:", ",").replace("CEP: ", ","))
            apply_category(Categories.BANK, item)
            yield item
