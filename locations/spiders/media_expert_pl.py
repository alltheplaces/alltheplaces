from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class MediaExpertPLSpider(Spider):
    name = "media_expert_pl"
    item_attributes = {"brand": "Media Expert", "brand_wikidata": "Q11776794"}
    start_urls = ["https://www.mediaexpert.pl/sklepy"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True  # Cloudflare geoblocking in use

    def parse(self, response: Response):
        yield JsonRequest(
            url="https://www.mediaexpert.pl/spark-state/{}".format(response.xpath('//*[@id="state"]/text()').get()),
            callback=self.parse_location,
        )

    def parse_location(self, response: Response):
        for branch in response.json()["Stores.StoresService.state"]["storesList"]:
            item = DictParser.parse(branch)
            if not item.get("housenumber"):
                item["street_address"] = item.pop("street")

            item["website"] = urljoin("https://www.mediaexpert.pl", branch["slug"])
            item["image"] = urljoin(
                "https://prod-api.mediaexpert.pl/api/images/filemanager_original/thumbnails/", branch["photo_path"]
            )

            try:
                item["opening_hours"] = self.parse_opening_hours(branch["open_hours"])
            except Exception:
                pass

            apply_category(Categories.SHOP_ELECTRONICS, item)

            yield item

    def parse_opening_hours(self, open_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for day_time in open_hours:
            oh.add_range(DAYS[day_time["week_day"] - 1], day_time["open_hour_from"], day_time["open_hour_to"])
        return oh
