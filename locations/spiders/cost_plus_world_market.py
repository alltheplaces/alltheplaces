from typing import Any, Iterable

from scrapy import Selector
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CostPlusWorldMarketSpider(JSONBlobSpider):
    name = "cost_plus_world_market"
    item_attributes = {"brand": "World Market", "brand_wikidata": "Q5174750"}
    allowed_domains = ["www.worldmarket.com"]
    start_urls = [
        "https://www.worldmarket.com/on/demandware.store/Sites-World_Market-Site/en_US/Stores-FindStores?postalCode=90001&radius=3000&showMap=false"
    ]
    locations_key = "stores"

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["name"] = None
        item["website"] = response.urljoin(location["storeExternalLink"])

        item["opening_hours"] = OpeningHours()
        for row in Selector(text="<ul>" + location["storeHours"] + "</ul>").xpath("//li"):
            cells = [t.strip() for t in row.xpath(".//span/text()").getall() if t.strip()]
            if len(cells) != 2:
                continue
            day = sanitise_day(cells[0].rstrip(":"), DAYS_EN)
            if not day:
                continue
            if cells[1].lower() == "closed":
                item["opening_hours"].set_closed(day)
            else:
                open_time, close_time = cells[1].split(" - ")
                item["opening_hours"].add_range(day, open_time, close_time, time_format="%I:%M %p")

        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)

        yield item
