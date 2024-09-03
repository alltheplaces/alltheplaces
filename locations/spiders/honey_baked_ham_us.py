from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours, DAYS
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class HoneyBakedHamUSSpider(Spider):
    name = "honey_baked_ham_us"
    item_attributes = {"brand": "Honey Baked Ham", "brand_wikidata": "Q5893363", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["api.honeybaked.com"]

    def start_requests(self) -> Iterable[JsonRequest]:
        for lat, lon in country_iseadgg_centroids(["US"], 94):
            yield JsonRequest(f"https://api.honeybaked.com/api/store/v1/?long={lon}&lat={lat}&radius=100")

    def parse(self, response: Response) -> Iterable[Feature]:
        features = response.json()

        if len(features) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

        if len(features) >= 100:
            raise RuntimeError(
                "Locations have probably been truncated due to 100 (or more) locations being returned by a single geographic radius search, and the API restricts responses to 100 results only. Use a smaller search radius."
            )

        for feature in features:
            attributes = feature["storeInformation"]
            item = DictParser.parse(attributes)
            item["branch"] = attributes["name"]
            item.pop("name", None)
            item["lat"] = attributes["location"]["coordinates"][1]
            item["lon"] = attributes["location"]["coordinates"][0]
            item["street_address"] = clean_address([attributes["address1"], attributes["address2"]])
            item["website"] = "https://www.honeybaked.com/stores/" + attributes["storeId"]

            item["opening_hours"] = OpeningHours()
            days_from_sunday = DAYS[-1:] + DAYS[:-1]
            for day_hours in attributes["storeHours"]:
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(days_from_sunday[day_hours["dayOfTheWeek"]], day_hours["openTime"], day_hours["closeTime"])

            yield item
