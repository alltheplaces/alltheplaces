import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class RdcGroupSpider(Spider):
    name = "rdc_group"
    item_attributes = {"operator": "RDC", "operator_wikidata": "Q11285807"}
    skip_auto_cc_domain = True
    start_urls = [
        "https://www.rdcgroup.co.jp/search/index.html?search=&category%5B%5D=1&category%5B%5D=2&category%5B%5D=3"
    ]

    def parse(self, response: Response):
        coords = {
            ref: (lat, lon)
            for ref, lat, lon in re.findall(
                r"\['shop_id'\] = (\d+);\s*shop\[\d+\]\['lat'\] = '([^']*)';\s*shop\[\d+\]\['lng'\] = '([^']*)'",
                response.text,
            )
        }
        for shop in response.css(".p-search-result__shop li"):
            item = Feature()
            item["website"] = response.urljoin(shop.css("a::attr(href)").get())
            item["ref"] = item["website"].split("id=")[1]
            item["name"] = shop.css(".p-search-result__shop__name::text").get()
            item["addr_full"] = shop.css(".p-search-result__shop__addr::text").get().removeprefix("海外・その他")
            item["lat"], item["lon"] = coords[item["ref"]]
            if "がってん寿司" in item["name"] or "合点寿司" in item["name"]:
                item["brand"] = "がってん寿司"
                item["brand_wikidata"] = "Q124499917"
                item["extras"]["cuisine"] = "sushi"
            apply_category(Categories.RESTAURANT, item)
            yield item
