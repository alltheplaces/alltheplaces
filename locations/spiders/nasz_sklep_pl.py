from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class NaszSklepPLSpider(Spider):
    name = "nasz_sklep_pl"
    brands = {
        "Delikatesy Premium": {"brand": "Delikatesy Premium", "brand_wikidata": "Q120147483"},
        "Delikatesy Sezam": {"brand": "Delikatesy Sezam", "brand_wikidata": "Q120173828"},
        "Livio": {"brand": "Livio", "brand_wikidata": "Q108599511"},
        "Nasz Sklep": {"brand": "Nasz Sklep", "brand_wikidata": "Q62070369"},
    }
    start_urls = ["https://nasz-sklep.pl/sklepy-wlasne/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//table//tr[position()>1]"):
            item = Feature()
            brand, item["street_address"], oh, item["phone"], item["email"] = location.xpath("td/text()").getall()
            item["ref"] = item["email"].split("@", 1)[0]
            if b := self.brands.get(brand):
                item.update(b)
            else:
                self.crawler.stats.inc_value("{}/unmapped_brand/{}".format(self.name, brand))
            yield item
