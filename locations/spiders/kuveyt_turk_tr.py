from urllib.parse import urlencode, urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class KuveytTurkTRSpider(Spider):
    name = "kuveyt_turk_tr"
    item_attributes = {"brand": "Kuveyt Türk", "brand_wikidata": "Q6036058"}
    allowed_domains = ["kuveytturk.com.tr"]
    base_url = "https://www.kuveytturk.com.tr/"

    def start_requests(self):
        yield Request(urljoin(self.base_url, "/en/branches-and-atms"))

    def parse(self, response, **kwargs):
        endpoint = response.xpath('//script[contains(text(), "addresses")]/text()').re_first(r'"bnh":"(.+?)"')
        params = {"p6": 0}  # Branches
        yield JsonRequest(urljoin(self.base_url, endpoint + "&" + urlencode(params)), callback=self.parse_pois)
        params["p6"] = 1  # ATMs
        yield JsonRequest(urljoin(self.base_url, endpoint + "&" + urlencode(params)), callback=self.parse_pois)
        params["p6"] = 2  # XTMs (a special type of ATMs)
        yield JsonRequest(urljoin(self.base_url, endpoint + "&" + urlencode(params)), callback=self.parse_pois)

    def parse_pois(self, response, **kwargs):
        pois = response.json()
        for poi in pois:
            item = DictParser.parse(poi)
            item["ref"] = poi.get("MapKey")
            if poi.get("LocationType") == "Branch":
                apply_category(Categories.BANK, item)
            elif poi.get("LocationType") in ["ATM", "XTM"]:
                apply_category(Categories.ATM, item)
            yield item
