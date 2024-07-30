import datetime
import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class HomegoodsSpider(SitemapSpider):
    name = "homegoods"
    item_attributes = {
        "brand": "HomeGoods",
        "brand_wikidata": "Q5887941",
        "country": "US",
    }
    sitemap_urls = ["https://www.homegoods.com/us/store/xml/storeLocatorSiteMap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.homegoods\.com\/us\/store\/stores\/.+\/(\d+)\/aboutstore$",
            "parse",
        )
    ]
    user_agent = BROWSER_DEFAULT

    def parse_hours(self, hours):
        """Mon-Thu: 9am - 9pm, Black Friday: 8am - 10pm, Sat: 9am - 9pm, Sun: 10am - 8pm"""
        opening_hours = OpeningHours()
        hours = hours.replace("Black Friday", "Fri")

        for x in hours.split(","):
            days, hrs = x.split(":", 1)
            try:
                open_time, close_time = hrs.split("-")
            except:
                continue
            open_time = open_time.replace("a", "am").replace("p", "pm")
            close_time = close_time.replace("a", "am").replace("p", "pm")

            if ":" in open_time:
                open_time = datetime.datetime.strptime(open_time.strip(), "%I:%M%p").strftime("%H:%M")
            else:
                open_time = datetime.datetime.strptime(open_time.strip(), "%I%p").strftime("%H:%M")

            if ":" in close_time:
                close_time = datetime.datetime.strptime(close_time.strip(), "%I:%M%p").strftime("%H:%M")
            else:
                close_time = datetime.datetime.strptime(close_time.strip(), "%I%p").strftime("%H:%M")

            if "-" in days:
                start_day, end_day = days.split("-")
                for day in DAYS[DAYS.index(start_day.strip()) : DAYS.index(end_day.strip()) + 1]:
                    opening_hours.add_range(day[:2], open_time=open_time, close_time=close_time)

            else:
                day = days.strip()[:2]
                opening_hours.add_range(day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse(self, response):
        item = Feature()

        item["name"] = response.xpath('//input[@name="storeName"]/@value').get()
        item["opening_hours"] = self.parse_hours(response.xpath('//input[@name="hours"]/@value').get())
        item["street_address"] = response.xpath('//input[@name="address"]/@value').get()
        item["city"] = response.xpath('//input[@name="city"]/@value').get()
        item["state"] = response.xpath('//input[@name="state"]/@value').get()
        #  item["postcode"] = response.xpath('//input[@name="zip"]/@value').get()
        if postcode := re.search(r" \w\w (\d+): ", response.xpath("//title/text()").get()):
            item["postcode"] = postcode.group(1)
        item["phone"] = response.xpath('//input[@name="phone"]/@value').get()
        item["lat"] = response.xpath('//input[@name="lat"]/@value').get()
        item["lon"] = response.xpath('//input[@name="long"]/@value').get()

        item["website"] = item["ref"] = response.url

        yield item
