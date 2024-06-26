from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class Zoloto585RUSpider(SitemapSpider):
    name = "zoloto_585_ru"
    item_attributes = {"brand_wikidata": "Q125730875"}
    sitemap_urls = ["https://zoloto585.ru/robots.txt"]
    sitemap_rules = [(r"/about/address/[^/]+/[^/]+/$", "parse")]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["lat"], item["lon"] = response.xpath("//@data-geo").get().split(",")
        item["street_address"] = response.xpath(
            '//div[@class="shop-info__item shop-info__item--address"]/span/text()'
        ).get()
        item["image"] = response.urljoin(
            response.xpath('//div[contains(@class, "address-block__shop-gallery")]/img/@src').get()
        )
        yield item
