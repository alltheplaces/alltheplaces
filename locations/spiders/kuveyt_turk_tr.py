from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class KuveytTurkTRSpider(Spider):
    name = "kuveyt_turk_tr"
    item_attributes = {"brand": "Kuveyt Türk", "brand_wikidata": "Q6036058"}
    allowed_domains = ["kuveytturk.com.tr"]

    def start_requests(self):
        url = "https://www.kuveytturk.com.tr/en/branches-and-atms"
        yield Request(url)

    def parse(self, response, **kwargs):
        bnh = response.xpath('//script[contains(text(), "addresses")]/text()').re_first(r'"bnh":"(.+?)"')
        base_url = "https://www.kuveytturk.com.tr/"
        yield JsonRequest(url=base_url + bnh + "&" + urlencode({"p6": 0}), callback=self.parse_pois)  # Branches
        yield JsonRequest(url=base_url + bnh + "&" + urlencode({"p6": 1}), callback=self.parse_pois)  # ATMs
        yield JsonRequest(
            url=base_url + bnh + "&" + urlencode({"p6": 2}), callback=self.parse_pois  # XTMs (a special type of ATMs)
        )

    def parse_pois(self, response, **kwargs):
        data = response.json()
        for poi in data:
            item = DictParser.parse(poi)
            item["ref"] = poi.get("MapKey")
            if poi.get("LocationType") == "Branch":
                apply_category(Categories.BANK, item)
            elif poi.get("LocationType") == "ATM":
                apply_category(Categories.ATM, item)
            elif poi.get("LocationType") == "XTM":
                apply_category(Categories.ATM, item)
            yield item
