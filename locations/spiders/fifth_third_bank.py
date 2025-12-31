import json
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class FifthThirdBankSpider(CrawlSpider):
    name = "fifth_third_bank"
    item_attributes = {
        "brand": "Fifth Third Bank",
        "brand_wikidata": "Q1411810",
    }
    allowed_domains = [
        "53.com",
    ]
    start_urls = [
        "https://locations.53.com",
    ]
    drop_attributes = {"image"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//*[@class="Directory-listItem"]')),
        Rule(LinkExtractor(allow=r"/\w+/[^/]+\.html", restrict_xpaths='//*[@class="Directory-listItem"]')),
        Rule(
            LinkExtractor(
                allow=r"/\w+/[^/]+/[^/]+\.html",
                restrict_xpaths='//*[@class="Directory-listTeaser Directory-listTeaser--noBorder"]',
            ),
            callback="parse",
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@class="LocationName-geo"]/text()').get()
        item["city"] = response.xpath('//*[@class="c-address-city"]/text()').get()
        item["street_address"] = response.xpath('//*[@class="c-address-street-1"]/text()').get()
        item["state"] = response.xpath('//*[@class="c-address-state"]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/@content').get()
        item["ref"] = item["website"] = response.url
        apply_category(Categories.BANK, item)
        if atm_info := response.xpath('//*[@class="atm-num"]//text()').get():
            apply_yes_no(Extras.ATM, item, True if "ATM" in atm_info else False)
        oh = OpeningHours()
        for day, time in json.loads(response.xpath("//@data-days").get()).items():
            day = day.replace("Hours", "")
            if time:
                if time == "Closed":
                    oh.set_closed(day)
                else:
                    open_time, close_time = time.split("-")
                    if ":" not in open_time:
                        open_time = open_time.replace("am", ":00am")
                    if ":" not in close_time:
                        close_time = close_time.replace("pm", ":00pm")
                    oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%I:%M%p")
        item["opening_hours"] = oh
        yield item
