from typing import Any
import scrapy
from scrapy.http import Response

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_phone

class AnacondaAUSpider(scrapy.Spider):
    name = "anaconda_au"
    item_attributes = {"brand": "Anaconda", "brand_wikidata": "Q105981238"}
    start_urls = ["https://www.anacondastores.com/sitemap/store/store-sitemap.xml"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "REDIRECT_ENABLED" : True
    }
    handle_httpstatus_list = [302]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token_request_url = str(response.headers.getlist("Location")[0].decode("utf-8"))
        yield scrapy.Request(url=token_request_url,callback=self.parse_token_request)

    def parse_token_request(self,response):
        token_request_url = str(response.headers.getlist("Location")[0].decode("utf-8"))
        yield scrapy.Request(url=token_request_url, callback=self.parse_token)

    def parse_token(self,response):
        url = str(response.headers.getlist("Location")[0].decode("utf-8"))
        token = str(response.headers.getlist("Set-Cookie")[0].decode("utf-8"))
        yield scrapy.Request(url=url,headers={"cookie":token}, callback=self.parse_store_urls)

    def parse_store_urls(self,response,**kwargs):
        for link in response.xpath('//urlset//url//loc/text()').getall():
            yield scrapy.Request(url = link, callback=self.parse_store)


    def parse_store(self, response):
        properties = {
            "ref": response.xpath('//div[contains(@id, "maps_canvas")]/@data-storeid').extract_first(),
            "name": response.xpath('//div[contains(@id, "maps_canvas")]/@data-storename').extract_first(),
            "lat": response.xpath('//div[contains(@id, "maps_canvas")]/@data-latitude').extract_first(),
            "lon": response.xpath('//div[contains(@id, "maps_canvas")]/@data-longitude').extract_first(),
            "addr_full": " ".join(
                " ".join(response.xpath('//div[contains(@class, "store-detail-desc")]/ul/li/text()').extract()).split()
            ),
            "country": "AU",
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_phone(properties, response)
        hours_raw = (
            " ".join(
                response.xpath(
                    '//div[contains(@class,"store-detail")]/div[2]/div[2]/div/table/tbody/tr/td/text()'
                ).extract()
            )
            .replace("Closed", "0:00am to 0:00am")
            .replace("to", "")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if day[1] == "0:00am" and day[2] == "0:00am":
                continue
            properties["opening_hours"].add_range(DAYS_EN[day[0]], day[1].upper(), day[2].upper(), "%I:%M%p")
        yield Feature(**properties)
