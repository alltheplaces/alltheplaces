import urllib
from typing import Any

import scrapy
from scrapy.http import Response

from locations.google_url import url_to_coords
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TheBodyShopTWSpider(scrapy.Spider):
    name = "the_body_shop_tw"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    start_urls = ["https://shop.thebodyshop.com.tw/pages/retail-stores-searching"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # location details displayed on the web page are actually images.
        for store_url in response.xpath('//a[contains(@href, "maps")]/@href').getall():
            item = Feature()
            item["ref"] = item["addr_full"] = clean_address(
                urllib.parse.unquote(store_url.split("/place/")[1].split("/")[0])
            )
            item["lat"], item["lon"] = url_to_coords(store_url)
            yield item
