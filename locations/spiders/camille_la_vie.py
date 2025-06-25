from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CamilleLaVieSpider(CrawlSpider):
    name = "camille_la_vie"
    item_attributes = {"brand": "Camille La Vie"}
    start_urls = ("https://camillelavie.com/pages/store-locations",)
    rules = [Rule(LinkExtractor(allow="/blogs/stores/"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = self.item_attributes["brand"]
        item["branch"] = response.xpath("//h1//text()").get().removeprefix("Camille La Vie Dresses at ")
        item["street_address"] = response.xpath('//*[@class="arcticle_description"]//p/span[2]/text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="arcticle_description"]//p/span[3]/text()').get()]
        )
        item["website"] = item["ref"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
