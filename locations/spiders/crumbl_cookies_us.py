from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CrumblCookiesUSSpider(Spider):
    name = "crumbl_cookies_us"
    item_attributes = {"brand": "Crumbl Cookies", "brand_wikidata": "Q106924414"}
    start_urls = ["https://crumblcookies.com/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        next_build_id = response.xpath("//script[contains(@src, '_ssgManifest.js')]/@src").get().split("/")[3]
        url = f"https://crumblcookies.com/_next/data/{next_build_id}/en-US/stores.json"
        yield JsonRequest(url=url, callback=self.parse_api)

    def parse_api(self, response, **kwargs):
        for location in response.json()["pageProps"]["stores"]:
            item = DictParser.parse(location)
            item["website"] = urljoin("https://crumblcookies.com/", location["slug"])
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["storeHours"]["description"])
            yield item
