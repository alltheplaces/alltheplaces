import re
from typing import Any

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_BR, OpeningHours, day_range, sanitise_day
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
        for location in chompjs.parse_js_object(re.search(r"RR\s*=\s*(\[.+\]),\s*PR=\(\)", response.text).group(1)):
            item = Feature()
            item["branch"] = location["nome"].removeprefix("CPQ ")
            item["addr_full"] = item["ref"] = location["endereco"]
            item["city"] = location["cidade"]
            item["state"] = location["estado"]
            oh = OpeningHours()
            for day_time in location["horario_funcionamento"].split(";"):
                day, time = day_time.split(": ")
                if " a " in day:
                    start_day, end_day = day.split(" a ")
                    start_day = sanitise_day(start_day, DAYS_BR)
                    end_day = sanitise_day(end_day, DAYS_BR)
                    open_time, close_time = time.split(" - ")
                    oh.add_days_range(day_range(start_day, end_day), open_time, close_time)

            item["opening_hours"] = oh

            apply_category(Categories.CAFE, item)

            yield item
