import json
from typing import Iterable

from scrapy import Request, Selector, Spider
from scrapy.http import FormRequest, Response

from locations.items import Feature


class PepcoSpider(Spider):
    name = "pepco"
    item_attributes = {"brand": "Pepco", "brand_wikidata": "Q11815580"}

    # Shop data is split into two places. The map data on https://pepco.eu/find-store/ contains only the shop ID and
    # geocoordinates. The shop name and address come from a shop listing which is requested from
    # https://pepco.eu/wp-admin/admin-ajax.php.
    #
    # To connect the data sets, first request all pages from https://pepco.eu/wp-admin/admin-ajax.php, passing along the
    # collected shop details. When no more pages are found, request https://pepco.eu/find-store/ and combine the data in
    # the parse() method.

    def get_shop_detail_request(self, page: int, shop_details: list[str]):
        return FormRequest(
            "https://pepco.eu/wp-admin/admin-ajax.php",
            formdata={"action": "get_more_shops", "search": "", "page": str(page)},
            callback=self.parse_shop_details,
            cb_kwargs={"shop_details": shop_details},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.get_shop_detail_request(0, [])

    def parse_shop_details(self, response, shop_details: list[str] = None):
        result = response.json()
        shop_details += result["shops"]
        next_page = result["page"]
        if result["last_page"]:
            shop_selector = Selector(text="".join(shop_details))
            yield Request("https://pepco.eu/find-store/", callback=self.parse, cb_kwargs={"shops": shop_selector})
        else:
            yield self.get_shop_detail_request(next_page, shop_details)

    def parse(self, response: Response, shops: Selector = None) -> Iterable[Feature]:
        for location in json.loads(response.xpath("//@shops-map-markers").get()):
            yield Feature(
                ref=location["shop_id"],
                lat=location["coordinates"]["lat"],
                lon=location["coordinates"]["lng"],
                name=shops.xpath(
                    '//div[@shops-map-marker-anchor="{}"]//@data-shop-name'.format(location["shop_id"])
                ).get(),
                addr_full=shops.xpath(
                    '//div[@shops-map-marker-anchor="{}"]//@data-shop-address'.format(location["shop_id"])
                ).get(),
            )
