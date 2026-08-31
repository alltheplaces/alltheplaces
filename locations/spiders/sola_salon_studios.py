from typing import Any, Iterable

from chompjs import parse_js_object
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SolaSalonStudiosSpider(SitemapSpider):
    name = "sola_salon_studios"
    item_attributes = {"brand": "Sola Salons", "brand_wikidata": "Q64337426"}
    sitemap_urls = ["https://www.solasalonstudios.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        location = data["props"]["pageProps"]["locationData"].get("data")
        if not location or location.get("demo_location"):
            return
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["street_address"] = clean_address([location.get("address_1"), location.get("address_2")])
        item["website"] = response.url
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
