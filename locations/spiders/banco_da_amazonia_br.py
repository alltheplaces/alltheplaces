from typing import Any, Iterable

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.react_server_components import parse_rsc


class BancoDaAmazoniaBRSpider(JSONBlobSpider):
    name = "banco_da_amazonia_br"
    item_attributes = {"brand": "Banco da Amazônia", "brand_wikidata": "Q16496429"}
    start_urls = ["https://www.bancoamazonia.com.br/o-banco/nossas-agencias"]

    def extract_json(self, response: Response) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for n, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        return DictParser.get_nested_key(dict(parse_rsc(rsc.encode())), "agencies")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("tag"):  # PARCEIROS-* banking correspondents hosted by partner organisations
            return

        item.pop("name")
        item["country"] = "BR"
        item["addr_full"] = clean_address(item["addr_full"].replace("Bairro:", ",").replace("CEP: ", ","))

        apply_category(Categories.BANK, item)

        yield item
