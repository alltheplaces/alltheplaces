from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CamilleLaVieUSSpider(CrawlSpider):
    name = "camille_la_vie_us"
    item_attributes = {"brand": "Camille La Vie"}
    start_urls = ("https://camillelavie.com/pages/store-locations",)
    rules = [Rule(LinkExtractor(allow="/pages/", restrict_xpaths='//*[@class="store_location"]'), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = self.item_attributes["brand"]

        base = response.xpath('//*[@class="arcticle_description"]')
        item["branch"] = base.xpath(".//p/span/text()").get("").strip() or base.xpath(".//div/text()").get()
        item["addr_full"] = (
            merge_address_lines(base.xpath(".//p/span/text()")[1:3].getall())
            or merge_address_lines(base.xpath(".//div/text()")[1:3].getall()).split(" Phone:")[0]
        )
        item["phone"] = (
            base.xpath('.//a[contains(@href, "tel:")]/@href').get()
            or base.xpath('.//*[contains(text(), "Phone:")]/text()').get()
        )

        item["website"] = item["ref"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
