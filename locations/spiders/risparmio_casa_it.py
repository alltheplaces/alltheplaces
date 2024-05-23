from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RisparmioCasaITSpider(Spider):
    name = "risparmio_casa_it"
    item_attributes = {
        "brand": "Risparmio Casa",
        "brand_wikidata": "Q125936928",
        "extras": Categories.SHOP_HOUSEWARE.value,
    }

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.risparmiocasa.com/wp-json/wp/v2/stores?per_page=100&page={}".format(page),
            meta={"page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for page in response.json():
            yield Request(page["link"], self.parse_page)

        if len(response.json()) == 100:
            yield self.make_request(response.meta["page"] + 1)

    def parse_page(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["addr_full"] = merge_address_lines(
            response.xpath('//div[@class="store_locator_single_address"]/text()').getall()
        )
        item["phone"] = response.xpath('//div[@class="phone_container"]/a/@href').get()
        self.crawler.stats.inc_value(
            "{}/{}".format(self.name, response.xpath('//div[@class="store_locator_single_categories"]/text()').get())
        )

        yield item
