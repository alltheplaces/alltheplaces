import json
import re
from json import JSONDecoder
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

RSC_CHUNK = re.compile(r'push\(\[1,("(?:[^"\\]|\\.)*")\]\)')


class SolaSalonStudiosSpider(SitemapSpider):
    name = "sola_salon_studios"
    item_attributes = {"brand": "Sola Salons", "brand_wikidata": "Q64337426"}
    sitemap_urls = ["https://www.solasalonstudios.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        payload = "".join(json.loads(chunk) for chunk in response.xpath("//script/text()").re(RSC_CHUNK))
        start = payload.find('"locationData":')
        if start < 0:
            return
        location = JSONDecoder().raw_decode(payload, start + 15)[0].get("data")
        if not location or location.get("demo_location") or location.get("operating_status") != "open":
            return
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["street_address"] = clean_address([location.get("address_1"), location.get("address_2")])
        item["website"] = response.url
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
