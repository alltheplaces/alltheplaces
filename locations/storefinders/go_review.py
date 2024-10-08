import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GoReviewSpider(CrawlSpider):
    """
    To use this spider, specify one or more start_urls,
    normally something like "https://hlinfo.goreview.co.za/store-locator"

    Override days if something other than DAYS_EN is required

    Also known as socialplaces.io or Social Places
    """

    custom_settings = {"ROBOTSTXT_OBEY": False}  # robots.txt disallows everything
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/.+\.goreview\.co\.za\/store-information.+$"),
            callback="parse",
        )
    ]
    days = DAYS_EN

    def parse(self, response):
        properties = {
            "ref": re.sub(r"\.goreview\.co\.za.*", "", re.sub(r"https:\/\/", "", response.url)),
            "branch": response.xpath('//div[@class="left-align-header"]/h2/text()')
            .get()
            .replace(self.item_attributes["brand"], "")
            .strip(),
            "addr_full": merge_address_lines(
                response.xpath('//div[contains(@class, "content-wrapper")]/div[2]/div[1]//p/text()').getall(),
            ),
            "phone": response.xpath(
                '//div[contains(@class, "content-wrapper")]/div[2]/div[3]//a[contains(@href, "tel:")]/@href'
            ).get(),
            "facebook": response.xpath(
                '//div[contains(@class, "content-wrapper")]/div[2]/div[5]//a[contains(@href, "facebook.com")]/@href'
            ).get(),
            "website": response.url,
        }
        if maps_links_js := response.xpath('//script[contains(text(), "#apple_maps_directions")]/text()').get():
            if "&sll=" in maps_links_js:
                properties["lat"], properties["lon"] = maps_links_js.split("&sll=", 1)[1].split("&", 1)[0].split(",", 2)
        hours_string = " ".join(
            response.xpath('//div[contains(@class, "content-wrapper")]/div[2]/div[4]/p//text()').getall()
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string, days=self.days)
        item = Feature(**properties)
        yield from self.post_process_item(item, response) or []

    def post_process_item(self, item, response):
        """Override with any post-processing on the item."""
        yield item
