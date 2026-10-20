from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class SigRoofingGBSpider(AmastyStoreLocatorSpider):
    name = "sig_roofing_gb"
    item_attributes = {"brand": "SIG Roofing", "brand_wikidata": "Q121435383"}
    allowed_domains = ["www.sigroofing.co.uk"]

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url="https://www.sigroofing.co.uk/amlocator/index/ajax/")

    def post_process_item(
        self, item: Feature, feature: dict, popup_html: Selector | None = None
    ) -> Iterable[Feature | Request]:
        item["branch"] = item.pop("name").removeprefix("SIG Roofing ").strip()
        if popup_html is not None:
            item["street_address"] = (
                popup_html.xpath('//text()[contains(., "Address:")]').get("").replace("Address:", "").strip()
            )
            item["postcode"] = (
                popup_html.xpath('//text()[contains(., "Postcode:")]').get("").replace("Postcode:", "").strip()
            )
            item["phone"] = popup_html.xpath('//a[starts-with(@href, "tel:")]/@href').get()
            item["email"] = popup_html.xpath('//a[starts-with(@href, "mailto:")]/@href').get()
        apply_category(Categories.SHOP_TRADE, item)
        yield Request(
            url=f"https://www.sigroofing.co.uk/amlocator/location/schedule/location_id/{feature['id']}/",
            callback=self.parse_hours,
            cb_kwargs={"item": item},
        )

    def parse_hours(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//div[contains(@class, "amlocator-row")]'):
            day = row.xpath('.//span[contains(@class, "-day")]/text()').get("").strip()
            times = row.xpath('.//span[contains(@class, "-time")]/text()').get("").strip()
            item["opening_hours"].add_ranges_from_string(f"{day} {times}", days=DAYS_EN)
        yield item
