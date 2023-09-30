from urllib.parse import urljoin

from scrapy import Spider

from locations.dict_parser import DictParser


class CrumblCookiesUSSpider(Spider):
    name = "crumbl_cookies_us"
    item_attributes = {"brand": "Crumbl Cookies", "brand_wikidata": "Q106924414"}
    start_urls = ["https://crumblcookies.com/_next/data/3BIqAAWyo9F7K-iV7dNy9/en-US/stores.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["pageProps"]["stores"]:
            location["street_address"] = location.pop("street")
            item = DictParser.parse(location)
            item["website"] = urljoin("https://crumblcookies.com/", location["slug"])
            item["extras"]["contact:yelp"] = location["yelpPage"]
            yield item
