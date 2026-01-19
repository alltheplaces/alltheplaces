import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GrandOpticalSpider(SitemapSpider, StructuredDataSpider):
    name = "grand_optical"
    item_attributes = {"brand": "GrandOptical", "brand_wikidata": "Q3113677"}
    sitemap_urls = ["https://www.grandoptical.com/sitemap.xml"]
    sitemap_rules = [(r"/opticien/[^/]+/\d+", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = response.url

        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        store = data["props"]["initialProps"]["pageProps"]["storeData"]
        item["lat"] = store["lat"]
        item["lon"] = store["lon"]

        apply_category(Categories.SHOP_OPTICIAN, item)

        yield item
