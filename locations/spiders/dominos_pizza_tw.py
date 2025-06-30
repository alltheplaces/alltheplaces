from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaTWSpider(SitemapSpider):
    name = "dominos_pizza_tw"
    item_attributes = {"brand_wikidata": "Q839466"}
    sitemap_urls = ["https://www.dominos.com.tw/sitemap.aspx"]
    sitemap_rules = [("tw/store/", "parse")]
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@class="storetitle"]/text()').get()
        item["addr_full"] = response.xpath('//*[@id="store-address-info"]//a').xpath("normalize-space()").get()
        item["lat"] = response.xpath('//*[@name="store-lat"]/@value').get()
        item["lon"] = response.xpath('//*[@name="store-lon"]/@value').get()
        item["ref"] = item["website"] = response.url
        yield item
