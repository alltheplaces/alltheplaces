from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class NaszSklepPLSpider(Spider):
    name = "nasz_sklep_pl"
    item_attributes = {"brand": "Nasz Sklep", "brand_wikidata": "Q62070369"}
    start_urls = ["https://nasz-sklep.pl/sklepy-wlasne/"]
    brands = {
        "DS": {"brand": "Delikatesy Sezam", "brand_wikidata": "Q120173828"},
        "Li": {"brand": "Livio", "brand_wikidata": "Q108599511"},
        "NS": {"brand": "Nasz Sklep", "brand_wikidata": "Q62070369"},
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//table//tr[position()>1]"):
            item = Feature()
            item["ref"] = location.xpath("td[1]/text()").get()
            item["city"] = location.xpath("td[2]/text()").get()
            item["street_address"] = location.xpath("td[3]/text()").get()
            item["email"] = location.xpath("td[4]//text()").get()
            item["phone"] = location.xpath("td[5]//text()").get()
            brand = item["ref"][0:2]
            if b := self.brands.get(brand):
                item.update(b)
            else:
                self.crawler.stats.inc_value("{}/unmapped_brand/{}".format(self.name, brand))
            yield item
