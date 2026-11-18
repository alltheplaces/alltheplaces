import json
import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_PT, OpeningHours, sanitise_day
from locations.items import Feature


class BancoMercantilBRSpider(Spider):
    name = "banco_mercantil_br"
    item_attributes = {"brand": "Banco Mercantil do Brasil", "brand_wikidata": "Q9645252"}
    # Any page with the map widget lists all stores in window.maps["map"]
    start_urls = ["https://encontre.bancomercantil.com.br/sao-paulo/jacarei/jacarei"]

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Request]:
        if not (match := re.compile(r'window\.maps\["map"\]\s*=\s*(\{.*?\});', re.DOTALL).search(response.text)):
            self.logger.error("Map data not found on %s", response.url)
            return
        for marker in json.loads(match.group(1))["markers"]:
            item = DictParser.parse(marker)
            item["branch"] = item.pop("name").removeprefix("Banco Mercantil - ")
            apply_category(Categories.BANK, item)
            yield Request(marker.pop("url"), callback=self.parse_card, cb_kwargs={"item": item})

    def parse_card(self, response: TextResponse, item: Feature, **kwargs: Any) -> Iterable[Feature]:
        item["website"] = response.url  # card redirects to the real store page
        if address := response.xpath('(//*[contains(@class, "address")])[1]//text()').getall():
            item["addr_full"] = " ".join(t.strip() for t in address if t.strip())
        item["opening_hours"] = self.parse_hours(response)
        yield item

    @staticmethod
    def parse_hours(response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        for row in response.xpath('//dl[@class="b-week"]/dt'):
            if not (day := sanitise_day(row.xpath("normalize-space(text())").get().split("-")[0], DAYS_PT)):
                continue
            for time_range in row.xpath("following-sibling::dd[1]/span/text()").getall():
                if (time_range := time_range.strip()) == "Fechado":
                    oh.set_closed(day)
                else:
                    open_time, _, close_time = time_range.partition("-")
                    oh.add_range(day, open_time, close_time)
        return oh
