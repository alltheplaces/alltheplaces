import re

import chompjs
import scrapy

from locations.items import Feature


class SmoothieKingKRSpider(scrapy.Spider):
    name = "smoothie_king_kr"
    item_attributes = {"brand": "Smoothie King", "brand_wikidata": "Q5491421"}
    start_urls = [
        "https://www.shinsegaefood.com/smoothieking/store/store.sf",
    ]

    def parse(self, response, **kwargs):
        pattern = re.compile("var storelist = (\\[.*\\])\\s*//console", re.DOTALL)
        data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var storelist = ")]/text()').re_first(pattern)
        )
        for store in data:
            item = Feature()
            item["name"] = store.get("title")
            item["addr_full"] = (
                re.search(r"주소\s*:(.*)<br.+영업시간", store["brandDesc"], re.DOTALL).group(1).replace("&nbsp;", "")
            )
            if m := re.search(r"전화번호 :(.*[0-9])", store.get("brandDesc")):
                item["phone"] = m.group()
            item["ref"] = store.get("seq")
            item["lon"], item["lat"] = re.search(r"(-?\d+.\d+),(-?\d+.\d+)", store.get("imgUrl"), re.DOTALL).groups()
            yield item
