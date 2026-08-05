import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class SvetoforRUSpider(Spider):
    name = "svetofor_ru"
    item_attributes = {"brand_wikidata": "Q61875920"}
    start_urls = ["https://svetoforonline.ru/shops/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for coords, balloon in re.findall(
            r'ymaps\.Placemark\(\[([\d.,-]+)\],\s*\{balloonContent:"(.*?)"\}', response.text
        ):
            item = Feature()
            item["lat"], item["lon"] = coords.split(",")
            item["addr_full"] = balloon.split("<br")[0].strip()
            item["ref"] = item["website"] = response.urljoin(Selector(text=balloon).xpath("//a/@href").get(""))
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
