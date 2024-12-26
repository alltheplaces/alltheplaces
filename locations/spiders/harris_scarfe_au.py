import html
import re
from typing import Any

import scrapy
import unicodedata
from scrapy.http import Response

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class HarrisScarfeAUSpider(scrapy.Spider):
    name = "harris_scarfe_au"
    item_attributes = {"brand": "Harris Scarfe", "brand_wikidata": "Q5665029"}
    start_urls = ["https://www.harrisscarfe.com.au/sitemap/store/store-sitemap.xml"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "REDIRECT_ENABLED": True
    }
    handle_httpstatus_list = [302]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token_request_url = str(response.headers.getlist("Location")[0].decode("utf-8"))
        yield scrapy.Request(url=token_request_url, callback=self.parse_token_request)

    def parse_token_request(self, response):
        token_request_url = str(response.headers.getlist("Location")[0].decode("utf-8"))
        yield scrapy.Request(url=token_request_url, callback=self.parse_token)

    def parse_token(self, response):
        url = str(response.headers.getlist("Location")[0].decode("utf-8"))
        token = str(response.headers.getlist("Set-Cookie")[0].decode("utf-8"))
        yield scrapy.Request(url=url, headers={"cookie": token}, callback=self.parse_store_urls)

    def parse_store_urls(self, response, **kwargs):
        for link in response.xpath('//urlset//url//loc/text()').getall():
            yield scrapy.Request(url=link, callback=self.parse_store)

    def parse_store(self, response):
        properties = {
            "ref": response.xpath('//div[@id="maps_canvas"]/@data-storeid').get(),
            "name": response.xpath('//div[@id="maps_canvas"]/@data-storename').get(),
            "lat": response.xpath('//div[@id="maps_canvas"]/@data-latitude').get(),
            "lon": response.xpath('//div[@id="maps_canvas"]/@data-longitude').get(),
            "addr_full": re.sub(
                r"\s{2,}",
                " ",
                unicodedata.normalize(
                    "NFKD",
                    html.unescape(
                        " ".join(
                            response.xpath('//div[contains(@class, "store-detail-desc")]/ul[1]/li/text()').getall()
                        )
                    ),
                )
                .replace("\n", " ")
                .strip(),
            ),
            "phone": response.xpath('//a[contains(@href, "tel:")]/text()').get().strip(),
            "website": response.url,
        }
        hours_string = " ".join(
            filter(None, response.xpath('//div[contains(@class, "store-detail")]/div[2]//table//td/text()').getall())
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
