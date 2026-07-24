from typing import AsyncIterator, Iterable

from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class FamiliaRUSpider(JSONBlobSpider):
    name = "familia_ru"
    item_attributes = {"brand": "Familia", "brand_wikidata": "Q127514809"}
    start_urls = ["https://www.famil.ru/cms/api/stores?where%5BisOn%5D%5Bequals%5D=true&limit=0&locale=ru"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    locations_key = "docs"

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url, dont_filter=True)

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("storeId")
        feature["city"] = feature["city"]["value"]["city"]
        if len(coordinates := feature.pop("coordinatesGroup", {}).get("coordinates", [])) == 2:
            feature["lon"], feature["lat"] = coordinates

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["phone"] = None
        item["state"] = None
        item["extras"]["check_date"] = feature["updatedAt"]

        if schedule := feature.get("schedule"):
            oh = OpeningHours()
            oh.add_ranges_from_string(
                schedule.replace(".", ""), DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, DELIMITERS_RU
            )
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
