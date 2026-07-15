from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, DAYS_FULL, OpeningHours


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
            item["website"] = urljoin("https://www.mediaexpert.pl", branch["slug"])
            try:
                oh = OpeningHours()
                for day_time in branch["open_hours"]:
                    oh.add_range(
                        day=DAYS_FROM_SUNDAY[day_time["week_day"]],
                        open_time=day_time["open_hour_from"],
                        close_time=day_time["open_hour_to"],
                    )
                item["opening_hours"] = oh
            except:
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
