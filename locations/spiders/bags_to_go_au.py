from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response, TextResponse
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class BagsToGoAUSpider(Spider):
    name = "bags_to_go_au"
    item_attributes = {"brand": "Bags To Go", "brand_wikidata": "Q117745930"}
    start_urls = ["https://bagstogo.com.au/pages/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//details[@id]"):
            item = Feature()
            item["city"] = location.xpath("./@id").get("").title()
            item["ref"] = location.xpath('.//a[contains(text(),"View")]/@href').get()
            item["branch"] = item["ref"].title().replace("-", " ")
            item["addr_full"] = response.xpath(f'//*[@data-title="{item["branch"]}"]/@data-address').get()
            item["website"] = urljoin("https://bagstogo.com.au/pages/", item["ref"])
            item["opening_hours"] = self.parse_opening_hours(location)
            extract_google_position(item, location)
            apply_category(Categories.SHOP_BAG, item)
            yield item

    def parse_opening_hours(self, location: TextResponse) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in location.xpath('.//*[contains(text(),"Opening hours")]/following-sibling::table/tr'):
            opening_hours.add_ranges_from_string(
                f"{rule.xpath('./td[1]/text()').get()}: {rule.xpath('./td[2]/text()').get()}"
            )
        return opening_hours
