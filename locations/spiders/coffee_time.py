import scrapy

from locations.dict_parser import DictParser
from scrapy.spiders import SitemapSpider
from locations.hours import DAYS, OpeningHours


class CoffeeTimeSpider(SitemapSpider):
    name = "coffeetime"
    item_attributes = {"brand": "Coffee Time"}
    allowed_domains = ["locations.coffeetime.com", "api.momentfeed.com"]
    sitemap_urls = ["https://locations.coffeetime.com/sitemap.xml"]
    sitemap_rules = [("", "parse")]

    def parse(self, response):
        headers = {"Host": "api.momentfeed.com", "Authorization": "YDGUJSNDOUAFKPRL"}
        url = "https://api.momentfeed.com/v1/analytics/api/llp.json?address={}"
        yield scrapy.Request(
            url=url.format(response.url.split("/")[-1].replace("-", "+").replace("_", ".")),
            headers=headers,
            callback=self.parse_store,
        )

    def parse_store(self, response):
        item = DictParser.parse(response.json()[0].get("store_info"))
        item["ref"] = response.json()[0].get("store_info", {}).get("corporate_id")
        item["website"] = f'https://{self.allowed_domains[0]}{response.json()[0].get("llp_url")}'

        oh = OpeningHours()
        for day in response.json()[0].get("store_info", {}).get("store_hours").split(";")[:-1]:
            info_day = day.split(",")
            oh.add_range(
                day=DAYS[int(info_day[0]) - 1],
                open_time=info_day[1],
                close_time=info_day[2],
                time_format="%H%M",
            )

        item["opening_hours"] = oh.as_opening_hours()

        yield item
