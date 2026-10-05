import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class WhittardGBSpider(Spider):
    name = "whittard_gb"
    item_attributes = {"brand": "Whittard of Chelsea", "brand_wikidata": "Q7996831"}
    start_urls = ["https://www.whittard.com/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath("//*[@data-store-finder-pin-data]"):
            item = Feature()
            item["ref"] = store.xpath("@data-store-handle").get()
            item["lat"] = store.xpath("@data-store-lat").get()
            item["lon"] = store.xpath("@data-store-lng").get()
            item["branch"] = re.sub(r"^Whittard of Chelsea\s+(?:at\s+)?", "", store.xpath("@data-store-name").get())
            item["addr_full"] = store.xpath("@data-store-address").get()
            item["phone"] = store.xpath("@data-store-phone").get()
            item["website"] = response.urljoin("/pages/stores/{}".format(item["ref"]))

            item["opening_hours"] = OpeningHours()
            card = response.xpath('//*[@data-store-finder-card][@data-store-handle="{}"]'.format(item["ref"]))
            for row in card.xpath(".//div[count(p) = 2]"):
                days, times = (row.xpath("normalize-space(p[{}])".format(i)).get() for i in (1, 2))
                if days and sanitise_day(days.split()[0]):
                    item["opening_hours"].add_ranges_from_string("{} {}".format(days, times))

            apply_category(Categories.SHOP_TEA, item)
            yield item
