import json
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class FoodstuffsNZSpider(Spider):
    name = "foodstuffs_nz"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    start_urls = ["https://www.newworld.co.nz/store-finder", "https://www.paknsave.co.nz/store-finder"]
    BRANDS = {"newworld": ("New World", "Q7012488"), "paknsave": ("PAK'nSAVE", "Q7125339")}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        for region in (DictParser.get_nested_key(data, "regionStoreGroupings") or {}).values():
            for group in region:
                for store in group.get("stores") or []:
                    yield response.follow(store["url"], callback=self.parse_store)

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        page = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]["page"]
        page.update(page.pop("contact_details") or {})

        item = DictParser.parse(page)
        item.pop("email", None)
        item.pop("state", None)
        item["website"] = response.url
        item["branch"] = item.pop("name").removeprefix("PAK'nSAVE ").removeprefix("New World ")
        item["brand"], item["brand_wikidata"] = self.BRANDS[response.url.split(".")[1]]

        item["opening_hours"] = OpeningHours()
        for day, times in (page.get("opening_hours") or {}).items():
            if times.get("closed"):
                item["opening_hours"].set_closed(day)
            elif times.get("open_from") and times.get("open_until"):
                try:
                    open_from = times["open_from"].replace(".", ":")
                    open_until = times["open_until"].replace(".", ":")
                    item["opening_hours"].add_range(day, open_from, open_until, "%I:%M%p")
                except ValueError:
                    pass

        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in (page.get("services") or []))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
