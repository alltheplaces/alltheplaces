import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature


class MosBurgerTWSpider(CrawlSpider):
    name = "mos_burger_tw"
    item_attributes = {"brand": "摩斯漢堡", "brand_wikidata": "Q1204169"}
    start_urls = ["https://www.mos.com.tw/shop/search.aspx"]
    rules = [
        Rule(
            LinkExtractor(allow=r"search_detail\.aspx\?id=\w+"),
            callback="parse",
        ),
        Rule(
            LinkExtractor(allow=r"search\.aspx\?area=_&page=\d+", restrict_xpaths='//*[contains(@id,"pagerNext")]'),
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.split("id=")[1]
        if match := re.search(r"LatLng\(([\d.-]+)[,\s]+([\d.-]+)\)", response.text):
            item["lat"], item["lon"] = match.groups()
        item["branch"] = response.xpath("//article/h2/text()").get()
        item["addr_full"] = response.xpath('//*[@class="address"]//text()').get()
        item["phone"] = response.xpath('//*[@class="tel"]//text()').get()
        item["website"] = response.url
        apply_category(Categories.FAST_FOOD, item)
        yield item
