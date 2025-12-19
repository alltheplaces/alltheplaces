from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature


class AwaySpider(Spider):
    name = "away"
    item_attributes = {"brand": "Away", "brand_wikidata": "Q48743138"}
    start_urls = ["https://www.awaytravel.com/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for button in response.xpath("//button[@data-mobile-store]"):
            location_name = button.xpath("./@data-mobile-store").get()
            footer = response.xpath(f"//div[@data-footer-store={location_name!r}]")
            if not footer:
                continue

            item = Feature()
            item["branch"] = location_name
            item["ref"] = button.xpath("./@data-href").get().removeprefix("/pages/store/")
            item["website"] = response.urljoin(button.xpath("./@data-href").get())
            item["lat"] = button.xpath("./@data-latitude").get()
            item["lon"] = button.xpath("./@data-longitude").get()

            item["image"] = response.urljoin(footer.xpath(".//div[@class='footer-store__image']/img/@src").get())
            item["phone"] = footer.xpath(".//a[starts-with(@href, 'tel:')]/@href").get()
            item["addr_full"] = footer.xpath(".//address/*/text()").get()

            yield item
