import re
from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.hours import DAYS_BR, OpeningHours
from locations.items import Feature


class CasaDoPaoDeQueijoBRSpider(scrapy.Spider):
    name = "casa_do_pao_de_queijo_br"
    item_attributes = {"brand": "Casa do Pão de Queijo", "brand_wikidata": "Q9698946"}
    start_urls = ["https://www.casadopaodequeijo.com.br/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        js_path = response.xpath('//*[@type = "module"]//@src').get()
        yield scrapy.Request(url="https://www.casadopaodequeijo.com.br" + js_path, callback=self.parse_location)

    def parse_location(self, response):
        raw_data = chompjs.parse_js_object(re.search(r"Hb=(\[.+\]),Gb=\(\)", response.text).group(1))
        for location in raw_data:
            item = Feature()
            item["name"] = location["nome"]
            item["addr_full"] = item["ref"] = location["endereco"]
            item["city"] = location["cidade"]
            item["state"] = location["estado"]
            oh = OpeningHours()
            oh.add_ranges_from_string(location["horario_funcionamento"], DAYS_BR)
            item["opening_hours"] = oh
            yield item
