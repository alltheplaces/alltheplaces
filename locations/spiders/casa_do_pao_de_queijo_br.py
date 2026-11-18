import re
from typing import Any

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
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
        match = re.search(r"=(\[\{nome:\"CPQ .+?\}\]),", response.text)
        if not match:
            self.logger.error("Could not find store data in bundle at %s", response.url)
            return
        for location in chompjs.parse_js_object(match.group(1)):
            item = Feature()
            item["branch"] = location["nome"].removeprefix("CPQ ")
            item["addr_full"] = item["ref"] = location["endereco"]
            item["city"] = location["cidade"]
            item["state"] = location["estado"]
            # "horario_funcionamento" is the same placeholder on every location, so it is not used
            apply_category(Categories.CAFE, item)

            yield item
