from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class MediaExpertPLSpider(Spider):
    name = "media_expert_pl"

    custom_settings = {"ROBOTSTXT_OBEY": False}

    requires_proxy = True  # Cloudflare geoblocking in use

    item_attributes = {"brand": "Media Expert", "brand_wikidata": "Q11776794"}

    start_urls = ["https://www.mediaexpert.pl/sklepy"]

    def parse(self, response: Response):
        state_url = response.xpath('//*[@id="state"]/text()').get()
        yield JsonRequest(url=f"https://www.mediaexpert.pl/spark-state/{state_url}", callback=self.parse_location)

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
            else:
                for day_time in branch["open_hours"]:
                    oh.add_range(
                        day=DAYS_FULL[day_time["week_day"] - 1],
                        open_time=day_time["open_hour_from"],
                        close_time=day_time["open_hour_to"],
                    )
                item["opening_hours"] = oh

            yield item

    def parse_opening_hours(self, open_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for day_time in open_hours:
            oh.add_range(DAYS[day_time["week_day"] - 1], day_time["open_hour_from"], day_time["open_hour_to"])
        return oh
