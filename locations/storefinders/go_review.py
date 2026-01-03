import re
from typing import AsyncIterator, Iterable

from scrapy.http import Request, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GoReviewSpider(CrawlSpider):
    """
    GoReview is also known as socialplaces.io or Social Places.

    To use this spider, specify a URL in the 'start_urls' list attribute.
    Usually the expected URL is similar to
    "https://hlinfo.goreview.co.za/store-locator".

    Override 'days' if a language other than DAYS_EN is required.
    """

    start_urls: list[str] = []
    custom_settings: dict = {"ROBOTSTXT_OBEY": False}  # robots.txt disallows everything
    rules: list[Rule] = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/.+\.goreview\.co\.za\/store-information.+$"),
            callback="parse",
        )
    ]
    days: dict = DAYS_EN

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) != 1:
            raise ValueError("Specify one URL in the start_urls list attribute.")
            return
        yield Request(url=self.start_urls[0])

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = re.sub(r"\.goreview\.co\.za.*", "", re.sub(r"https:\/\/", "", response.url))

        branch_raw = response.xpath('//div[@class="left-align-header"]/h2/text()').get()
        if attribs := getattr(self, "item_attributes", None):
            if isinstance(attribs, dict):
                if brand_name := attribs.get("brand"):
                    item["branch"] = branch_raw.replace(brand_name, "").strip()

        item["addr_full"] = merge_address_lines(
            response.xpath('//div[contains(@class, "content-wrapper")]/div[2]/div[1]//p/text()').getall(),
        )

        item["phone"] = response.xpath(
            '//div[contains(@class, "content-wrapper")]/div[2]/div[3]//a[contains(@href, "tel:")]/@href'
        ).get()

        item["facebook"] = response.xpath(
            '//div[contains(@class, "content-wrapper")]/div[2]/div[5]//a[contains(@href, "facebook.com")]/@href'
        ).get()

        item["website"] = response.url
        if "?" in item["website"]:
            item["website"] = item["website"].split("?", 1)[0]

        if maps_links_js := response.xpath('//script[contains(text(), "#apple_maps_directions")]/text()').get():
            if "&sll=" in maps_links_js:
                item["lat"], item["lon"] = maps_links_js.split("&sll=", 1)[1].split("&", 1)[0].split(",", 2)

        hours_string = " ".join(
            response.xpath('//div[contains(@class, "content-wrapper")]/div[2]/div[4]/p//text()').getall()
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string, days=self.days)

        yield from self.post_process_item(item, response) or []

    def post_process_item(self, item: Feature, response: TextResponse) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
