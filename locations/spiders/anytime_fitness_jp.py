import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response, TextResponse

from locations.items import Feature
from locations.spiders.anytime_fitness import AnytimeFitnessSpider
from locations.structured_data_spider import StructuredDataSpider


class AnytimeFitnessJPSpider(StructuredDataSpider):
    name = "anytime_fitness_jp"
    item_attributes = AnytimeFitnessSpider.item_attributes
    allowed_domains = ["www.anytimefitness.co.jp"]
    search_for_twitter = False
    search_for_facebook = False

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.anytimefitness.co.jp/assets/map-static.xml", callback=self.parse_markers)

    def parse_markers(self, response: Response) -> Iterable[Request]:
        for marker in response.xpath("//marker"):
            # iconB marks clubs that are still preparing to open,
            # iconC clubs that are temporarily closed for renovation.
            if marker.xpath("@category").get() == "iconB":
                continue
            yield Request(
                response.urljoin(marker.xpath("@linkurl").get() + "/"),
                callback=self.parse_sd,
                meta={"marker": marker.attrib},
            )

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        marker = response.meta["marker"]
        item["ref"] = marker["postid"]
        item["branch"] = marker["name"].removeprefix("エニタイムフィットネス").strip().removesuffix("店")
        item.pop("name", None)
        # Some numbers use a katakana long vowel mark or carry a note,
        # e.g. "042ｰ638ｰ0125" or "0956-37-8653　＜毎週 木・日 曜日ノースタッフデー＞"
        if m := re.match(r"[\dｰ-]+", ld_data.get("telephone", "")):
            item["phone"] = m.group().replace("ｰ", "-")
        if item.get("email"):
            item["email"] = item["email"].split()[0]
        item["lat"] = marker["lat"]
        item["lon"] = marker["lng"]
        if marker["category"] == "iconC":
            # The page still lists 24/7 hours while the club is being renovated
            item.pop("opening_hours", None)
        yield item
