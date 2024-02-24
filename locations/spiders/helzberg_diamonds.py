import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class HelzbergDiamondsSpider(SitemapSpider):
    name = "helzberg_diamonds"
    item_attributes = {"brand": "Helzberg Diamonds", "brand_wikidata": "Q16995161"}
    allowed_domains = ["helzberg.com"]
    sitemap_urls = ["https://www.helzberg.com/sitemap_stores.xml"]
    sitemap_rules = [("", "parse")]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        item = Feature()
        address = response.xpath('//p[contains(@class,"address")]/text()').extract()
        item["ref"] = re.findall("[0-9]+", response.url)[0]
        item["name"] = response.xpath('//h1[@class="store-title"]/text()').get()
        item["phone"] = response.xpath('//a[@class="storelocator-phone"]/text()').get()
        item["website"] = response.url
        item["city"] = address[-3].replace("\n", "").split(",")[0]
        item["postcode"] = re.findall("[0-9]+", address[-3].replace("\n", "").split(",")[1])[0]
        item["state"] = re.findall("[A-Z]{2}", address[-3].replace("\n", "").split(",")[1])[0]
        item["street_address"] = (
            address[:-2][0].replace("\n", "") + address[:-2][1].replace("\n", "")
            if len(address[:-2]) > 2
            else address[:-2][0].replace("\n", "")
        ).strip()
        item["lat"], item["lon"] = re.findall(
            "[0-9]+.+", response.xpath('//a[contains(@class,"store-map")]/@href').get()
        )[0].split(",")
        days = response.xpath('//div[@class="store-hours"]/p/text()').extract()
        days.append(response.xpath('//main[@id="maincontent"]//b/text()').get())  # get and insert first_day
        oh = OpeningHours()
        for day in days:
            if "Closed" in day:
                continue
            oh.add_range(
                day=re.findall(r"[-\w]+", day)[0],
                open_time=re.findall(r"[0-9]+.+", day)[0].split(" - ")[0],
                close_time=re.findall(r"[0-9]+.+", day)[0].split(" - ")[1],
                time_format="%I:%M%p",
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
