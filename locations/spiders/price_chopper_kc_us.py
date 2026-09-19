from typing import Any
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# This is the Kansas City / Des Moines "Price Chopper" operated under
# license from Associated Wholesale Grocers by several independent
# ownership groups (Ball's Food Stores, Cosentino's, Queen's Price
# Chopper, McKeever's, etc). It is unrelated to the New England "Price
# Chopper" (Golub Corporation) already covered by golub_corporation_us.py.


class PriceChopperKcUSSpider(Spider):
    name = "price_chopper_kc_us"
    item_attributes = {"brand": "Price Chopper", "brand_wikidata": "Q7242572", "name": "Price Chopper"}
    allowed_domains = ["www.mypricechopper.com"]
    start_urls = ["https://www.mypricechopper.com/public/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            if not store.get("Active"):
                continue
            store["street_address"] = store.pop("Address1")
            item = DictParser.parse(store)
            item["website"] = urljoin(response.url, store["StoreDetailsPageUrl"])
            yield Request(url=item["website"], callback=self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response: Response, item: dict) -> Any:
        oh = OpeningHours()
        day_divs = response.xpath(
            "//div[@class='card-header bg-dark'][contains(., 'STORE HOURS')]/following-sibling::div[@class='card-body'][1]/div"
        )
        hours_text = " ".join(d.xpath("string(.)").get("").strip() for d in day_divs)
        if hours_text:
            oh.add_ranges_from_string(hours_text)
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
