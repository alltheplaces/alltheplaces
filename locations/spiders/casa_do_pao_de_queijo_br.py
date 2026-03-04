import re
from typing import Any

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_BR, OpeningHours
from locations.items import Feature


class CasaDoPaoDeQueijoBRSpider(Spider):
    name = "casa_do_pao_de_queijo_br"
    item_attributes = {"brand": "Casa do Pão de Queijo", "brand_wikidata": "Q9698946"}
    start_urls = ["https://www.casadopaodequeijo.com.br/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield Request(
            response.urljoin(response.xpath('//script[@type="module"]/@src').get()), callback=self.parse_location
        )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(re.search(r"Hb=(\[.+\]),Gb=\(\)", response.text).group(1)):
            item = Feature()
            item["name"] = location["nome"]
            item["addr_full"] = item["ref"] = location["endereco"]
            item["city"] = location["cidade"]
            item["state"] = location["estado"]
            oh = OpeningHours()
            oh.add_ranges_from_string(location["horario_funcionamento"], DAYS_BR)
            item["opening_hours"] = oh

            apply_category(Categories.CAFE, item)

            yield item
