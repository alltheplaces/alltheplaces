from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ChuysUSSpider(Spider):
    name = "chuys_us"
    item_attributes = {"brand": "Chuy's", "brand_wikidata": "Q5118415"}
    start_urls = ["https://www.chuys.com/locations-sitemap.xml"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.urls = {}
        for loc in iterloc(Sitemap(response.body)):
            self.urls[loc.rsplit("/", 1)[1]] = loc

        yield JsonRequest(
            url="https://www.chuys.com/api/restaurants", headers={"x-source-channel": "WEB"}, callback=self.parse_api
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["restaurants"]:
            location.update(location["contactDetail"].pop("address"))
            location.update(location["contactDetail"]["phoneDetail"].pop(0))
            item = DictParser.parse(location)
            item["country"] = location["country"]
            item["branch"] = location["restaurantName"]
            item["ref"] = location["restaurantNumber"]
            item["street_address"] = merge_address_lines([location.get("street1"), location.get("street2")])
            item["website"] = self.urls.get(str(location["restaurantNumber"]))
            yield item
