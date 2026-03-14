from json import loads
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class HairhouseAUSpider(SitemapSpider):
    name = "hairhouse_au"
    item_attributes = {"brand": "Hairhouse", "brand_wikidata": "Q118383855"}
    allowed_domains = ["www.hairhouse.com.au"]
    sitemap_urls = ["https://www.hairhouse.com.au/store/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.hairhouse\.com\.au\/store\/[^\/]+$", "parse")]
    # wanted_types = ["HealthAndBeautyBusiness"]

    def parse(self, response: Response) -> Iterable[Feature]:
        ldjson_blob = response.xpath('//script[@type="application/ld+json"]/text()').get()
        ldjson = loads(ldjson_blob)["script:ld+json"]
        item = LinkedDataParser.parse_ld(ldjson, time_format="%H:%M")
        item["branch"] = item.pop("name").removeprefix("Hairhouse ")
        item["addr_full"] = item.pop("street_address", None)
        item.pop("image", None)
        apply_category(Categories.SHOP_HAIRDRESSER_SUPPLY, item)
        yield item
