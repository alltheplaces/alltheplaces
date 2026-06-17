from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_SR, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BipaHRSpider(Spider):
    name = "bipa_hr"
    item_attributes = {"brand": "Bipa", "brand_wikidata": "Q864933"}
    start_urls = ["https://bipa.hr/poslovnice/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath("//div[contains(@class, 'marker')]"):
            item = Feature()
            item["branch"] = store.xpath("@data-name").get()
            item["lat"] = store.xpath("@data-lat").get()
            item["lon"] = store.xpath("@data-lng").get()
            item["street_address"] = store.xpath("./article/address/text()[1]").get()
            item["addr_full"] = merge_address_lines(store.xpath("./article/address/text()").getall())
            item["ref"] = store.xpath("./article/@class").get().split(" ", 1)[0]

            oh = OpeningHours()

            for day_time in store.xpath(".//ul//li"):
                day_time_string = day_time.xpath("normalize-space()").get()
                oh.add_ranges_from_string(day_time_string.strip(), days=DAYS_SR)
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_CHEMIST, item)

            yield item
