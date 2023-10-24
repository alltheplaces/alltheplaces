import json
from urllib.parse import urljoin, urlparse

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class JyskSpider(scrapy.Spider):
    name = "jysk"
    item_attributes = {"brand": "JYSK", "brand_wikidata": "Q138913"}
    start_urls = ["https://www.jysk.com/"]

    def parse(self, response):
        main_urls = response.xpath(
            "//div[contains(@class, 'col-xs-12 col-sm-4 col-md-4 panels-flexible-region-inside columns')][1]//li/a/@href"
        ).getall()

        # There are Jysk owned stores and Jysk franchise stores.
        # Only Jysk owned stores have standartized store locator, franchise stores have different website format.
        # For this spider we are interested only in Jysk owned stores. Others should be scraped with different spiders.
        # For reference:
        # franchise_urls = response.xpath(
        #     "//div[contains(@class, 'col-xs-12 col-sm-4 col-md-4 panels-flexible-region-inside columns')][2]//li/a/@href"
        # ).getall()
        for url in main_urls:
            self.logger.info("Found country site: %s", url)
            yield scrapy.Request(urljoin(url, "stores-locator"), callback=self.parse_country_site)

    def parse_country_site(self, response):
        data = response.xpath('//*[@id="stores-locator-ssr"]/div').attrib["data-jysk-react-properties"]
        locations = json.loads(data)["storesCoordinates"]
        self.logger.debug("Found %d locations on %s", len(locations), response.url)
        for location in locations:
            yield scrapy.Request(
                "https://{}/services/store/get/{}".format(urlparse(response.url).netloc, str(location["id"])),
                callback=self.parse_data,
                cb_kwargs=dict(locator_url=response.url),
            )

    def parse_data(self, response, locator_url):
        def convert(i):
            s = str(i)
            return s[:-2] + ":" + s[-2:]

        store = response.json()
        store["name"] = store.pop("shop_name")
        store["tel"] = store.pop("store_phone")
        store["house_number"] = store.pop("house")
        item = DictParser.parse(store)
        item["image"] = store.get("image")
        item["website"] = locator_url + "?storeId=" + store["shop_id"]
        item["ref"] = store["shop_id"]

        oh = OpeningHours()
        for info in store["opening"]:
            day_index = info["day"]
            if day_index == 0:
                day_index = 7
            start = info["starthours"]
            end = info["endhours"]
            if start and end:
                oh.add_range(DAYS_FULL[day_index - 1], convert(start), convert(end))
        item["opening_hours"] = oh
        yield item
