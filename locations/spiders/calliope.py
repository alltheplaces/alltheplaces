from typing import Any, Iterable

from scrapy import Request, Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature


class CalliopeSpider(Spider):
    name = "calliope"
    item_attributes = {"brand": "Calliope", "brand_wikidata": "Q125703464"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            "https://store.calliope.style/en?page={}&__xhr=1".format(page),
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()["results"]
        locations = Selector(text=data["items"])
        for location in locations.xpath('//div[@class="b-result"]'):
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["addr_full"] = location.xpath('./p[@class="b-result__address"]/text()').get()
            item["website"] = location.xpath("./div/h2/a/@href").get().split("?", 1)[0]
            item["phone"] = location.xpath('./p[@class="b-result__contact"]/a/text()').get()
            yield item

        if data["current_page"] < data["last_page"]:
            yield self.make_request(data["current_page"] + 1)
