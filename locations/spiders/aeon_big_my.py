import html
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AeonBigMYSpider(Spider):
    name = "aeon_big_my"
    item_attributes = {"brand": "AEON BiG", "brand_wikidata": "Q8077280"}
    allowed_domains = ["aeonbig.com.my"]
    start_urls = ["https://aeonbig.com.my/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//img[contains(@alt,"AEON BiG")]/ancestor::div[contains(@class,"rounded-xl")]'):
            if branch := location.xpath(".//img/@alt").get("").strip().removeprefix("AEON BiG "):
                item = Feature()
                item["ref"] = item["branch"] = branch
                item["website"] = response.url
                address = location.xpath('.//div[contains(@class,"p-5")]')
                item["state"] = address.xpath('./p[contains(@class,"inline-block")]/text()').get()
                item["addr_full"] = address.xpath('./p[contains(@class,"text-slate")]/text()').get()
                item["image"] = html.unescape(location.xpath(".//img/@src").get(""))
                item["phone"] = location.xpath('.//*[contains(text(),"Telephone")]/following-sibling::p/text()').get()
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(
                    location.xpath('.//*[contains(text(),"Business Hours")]/following-sibling::p/text()')
                    .get("")
                    .replace("& PH", "")
                )
                apply_category(Categories.SHOP_SUPERMARKET, item)
                yield item
