from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.selector import Selector
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BagsToGoAUSpider(Spider):
    name = "bags_to_go_au"
    item_attributes = {"name": "Bags To Go", "brand": "Bags To Go", "brand_wikidata": "Q117745930"}
    start_urls = ["https://bagstogo.com.au/pages/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//li[contains(@class, "accordion-item")]'):
            toggle = location.xpath('.//div[contains(@class, "accordion-toggle")]')
            item = Feature()
            item["branch"] = toggle.attrib.get("data-title")
            item["addr_full"] = toggle.attrib.get("data-address")
            try:
                # One store has a corrupt junk string in data-lat.
                item["lat"] = float(toggle.attrib.get("data-lat", ""))
                item["lon"] = float(toggle.attrib.get("data-lng", ""))
            except ValueError:
                pass
            item["state"] = location.attrib.get("data-area", "").upper()
            if image := toggle.attrib.get("data-img"):
                item["image"] = response.urljoin(image)
            item["ref"] = location.xpath('.//a[contains(text(), "View")]/@href').get()
            item["website"] = urljoin("https://bagstogo.com.au/pages/", item["ref"])
            item["opening_hours"] = self.parse_opening_hours(location)
            apply_category(Categories.SHOP_BAG, item)
            yield item

    def parse_opening_hours(self, location: Selector) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in location.xpath(".//table/tr"):
            opening_hours.add_ranges_from_string(
                f"{rule.xpath('./td[1]/text()').get()}: {rule.xpath('./td[2]/text()').get()}"
            )
        return opening_hours
