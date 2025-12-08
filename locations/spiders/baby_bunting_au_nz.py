from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BabyBuntingAUNZSpider(JSONBlobSpider):
    name = "baby_bunting_au_nz"
    item_attributes = {
        "brand": "Baby Bunting",
        "brand_wikidata": "Q109626935",
    }
    allowed_domains = ["www.babybunting.com.au"]
    start_urls = ["https://www.babybunting.com.au/api/cnts/getAllFromType"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.start_urls[0],
            data=[{"type": "store"}],
            method="POST",
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if (
            "CLOSED" in feature["title"]
            or "COMING SOON" in feature["title"]
            or len(list(filter(lambda h: ("CLOSED" in h.upper()), feature["opening_hours"].values())))
            == len(feature["opening_hours"].values())
        ):
            return

        item["ref"] = str(feature["supplychannel_id"])
        item["branch"] = feature["title"]
        item["lat"], item["lon"] = map(str.strip, feature["address_lat_lng"].split(",", 1))
        item["addr_full"] = feature["address_text"].replace("\xa0", " ")
        item["postcode"] = str(item["postcode"])
        item["website"] = "https://www.babybunting.com.au/find-a-store/" + item["website"]
        if "lat" in item and "lon" in item:
            if float(item["lon"]) > 166.42 and float(item["lat"]) < 34.42:
                item["country"] = "NZ"
                item.pop("state", None)

        # Note: hours are for the upcoming week and change run-by-run
        # depending on public holidays which are upcoming. Typical hours are
        # not provided in the API output and would have to be determined by
        # comparing historical runs of this spider.
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            open_key = day.lower() + "_from"
            close_key = day.lower() + "_to"
            if open_key in feature["opening_hours"] and close_key in feature["opening_hours"]:
                if feature["opening_hours"][open_key] == "CLOSED" or feature["opening_hours"][close_key] == "CLOSED":
                    item["opening_hours"].set_closed(DAYS_EN[day])
                else:
                    open_time = feature["opening_hours"][open_key].replace(" ", "").replace(".", ":")
                    close_time = feature["opening_hours"][close_key].replace(" ", "").replace(".", ":")
                    item["opening_hours"].add_range(DAYS_EN[day], open_time, close_time, "%I:%M%p")

        apply_category(Categories.SHOP_BABY_GOODS, item)
        yield item
