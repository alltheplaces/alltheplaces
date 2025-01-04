from json import loads
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class AesopSpider(SitemapSpider):
    name = "aesop"
    item_attributes = {"brand": "Aesop", "brand_wikidata": "Q4688560"}
    allowed_domains = ["www.aesop.com"]
    sitemap_urls = ["https://www.aesop.com/static/stores/en-AU.xml"]
    sitemap_rules = [("^https:\/\/www\.aesop\.com\/[a-z]{2}\/r\/[\w\-]+\/$", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        next_data = loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        apollo_state_key = list(
            filter(
                lambda x: x.startswith("StoreType:aesop-"), next_data["props"]["pageProps"]["__APOLLO_STATE__"].keys()
            )
        )
        if len(apollo_state_key) != 1:
            return
        store_data = next_data["props"]["pageProps"]["__APOLLO_STATE__"][apollo_state_key[0]]

        if store_data["type"] != "Signature Store":
            self.logger.error("Unhandled store type: " + store_data["type"])
            return

        item = DictParser.parse(store_data)
        if store_data.get("code"):
            item["ref"] = store_data["code"]
        else:
            # Fall back to using the URL slug as an identifier if the store
            # code is not provided.
            item["ref"] = store_data["id"]
        item["branch"] = item.pop("name", "").removeprefix("Aesop ")
        item["addr_full"] = store_data["formattedAddress"]
        item["street_address"] = store_data["address"]
        item["website"] = response.url

        if store_data.get("openingHours"):
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in store_data.get("openingHours").items():
                if day_name.title() not in DAYS_FULL:
                    continue
                if day_hours["closedAllDay"]:
                    item["opening_hours"].set_closed(day_name.title())
                    continue
                for period in [
                    ("openingTime", "closingTime"),
                    ("openingTime2", "closingTime2"),
                    ("openingTime3", "closingTime3"),
                ]:
                    if (
                        day_hours[f"{period[0]}Hour"] is None
                        or day_hours[f"{period[0]}Minute"] is None
                        or day_hours[f"{period[1]}Hour"] is None
                        or day_hours[f"{period[1]}Minute"] is None
                    ):
                        continue
                    start_time = day_hours[f"{period[0]}Hour"] + ":" + day_hours[f"{period[0]}Minute"].zfill(2)
                    close_time = day_hours[f"{period[1]}Hour"] + ":" + day_hours[f"{period[1]}Minute"].zfill(2)
                    item["opening_hours"].add_range(day_name.title(), start_time, close_time)

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item
