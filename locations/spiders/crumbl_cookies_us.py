from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class CrumblCookiesUSSpider(Spider):
    name = "crumbl_cookies_us"
    item_attributes = {"brand": "Crumbl Cookies", "brand_wikidata": "Q106924414"}
    start_urls = ["https://crumblcookies.com/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        nextBuildId = response.xpath("//script[contains(@src, '_ssgManifest.js')]/@src").get().split("/")[3]
        url = f"https://crumblcookies.com/_next/data/{nextBuildId}/en-US/stores.json"
        yield JsonRequest(url=url, callback=self.parse_api)

    def parse_api(self, response, **kwargs):
        for location in response.json()["pageProps"]["stores"]:
            location["street_address"] = location.pop("street")
            item = DictParser.parse(location)
            item["website"] = urljoin("https://crumblcookies.com/", location["slug"])
            item["extras"]["contact:yelp"] = location["yelpPage"]
            yield item
