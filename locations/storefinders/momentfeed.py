import urllib.parse
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
from locations.pipelines.address_clean_up import merge_address_lines


class MomentFeedSpider(Spider):
    """
    MomentFeed (owned by Uberall)
    https://momentfeed.com/

    To use, specify:
      - `api_key`: mandatory parameter
      - `page_size`: optional parameter, default value is 100
    """

    dataset_attributes: dict = {"source": "api", "api": "momentfeed.com"}
    api_key: str
    page_size: int = 100

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"https://uberall.com/api/mf-lp-adapter/llp.json?center=0,0&coordinates=-90,180,90,-180&pageSize={self.page_size}&page=1",
            headers={"Authorization": self.api_key},
        )

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature | JsonRequest]:
        if "message" in response.json():
            return

        for feature in response.json():
            store_info = feature["store_info"]
            item = DictParser.parse(store_info)
            item["ref"] = store_info["corporate_id"]
            item["street_address"] = merge_address_lines([store_info["address_extended"], store_info["address"]])
            item.pop("addr_full", None)
            item["extras"]["start_date"] = store_info["openingDate"]

            try:
                item["opening_hours"] = self.parse_opening_hours(store_info)
            except:
                self.logger.error("Error parsing opening hours")

            for provider in store_info["providers"]:
                if provider["_type"] == "Facebook":
                    set_social_media(item, SocialMedia.FACEBOOK, provider["url"])
                elif provider["_type"] == "Google" and provider.get("place_id"):
                    item["extras"]["ref:google:place_id"] = provider["place_id"]
                elif provider["_type"] == "Instagram":
                    if "/explore/locations/" not in provider["url"]:
                        set_social_media(item, SocialMedia.INSTAGRAM, provider["url"])
                elif provider["_type"] == "Yelp":
                    set_social_media(item, SocialMedia.YELP, provider["url"])
                elif provider["_type"] == "Foursquare":
                    set_social_media(item, "foursquare", provider["url"])

            yield from self.parse_item(item, feature, store_info)

        if len(response.json()) == self.page_size:
            next_page = int(urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)["page"][0]) + 1
            yield JsonRequest(
                url=f"https://uberall.com/api/mf-lp-adapter/llp.json?center=0,0&coordinates=-90,180,90,-180&pageSize={self.page_size}&page={next_page}",
                headers={"Authorization": self.api_key},
            )

    def parse_opening_hours(self, store_info: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in store_info["store_hours"].split(";"):
            rule = day.split(",")
            if len(rule) == 3:
                oh.add_range(DAYS[int(rule[0]) - 1], rule[1], rule[2].replace("2400", "2359"), "%H%M")
        return oh

    def parse_item(self, item: Feature, feature: dict, store_info: dict) -> Iterable[Feature]:
        yield item
