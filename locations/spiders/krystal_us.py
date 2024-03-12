import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class KrystalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "krystal_us"
    item_attributes = {"brand": "Krystal", "brand_wikidata": "Q472195"}
    allowed_domains = ["www.krystal.com"]
    sitemap_urls = ["http://www.krystal.com/sitemap.xml"]
    sitemap_rules = [(r"\/locations\/[a-z]{2}\/[\w\-]+\/[\w\-]+\/?$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        store_ref = response.xpath("//h1[1]/text()").get()
        if m := re.match(r"^KRYSTAL ([\w]+) \|", store_ref, re.IGNORECASE):
            item["ref"] = m.group(1)
        else:
            item["ref"] = response.url
        item["name"] = response.xpath("//title/text()").get().split(" | ", 1)[0]
        item["addr_full"] = " ".join(filter(None, response.xpath('//div[@class="center-box"]/p[1]/text()').getall()))
        item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        hours_columns = response.xpath('//div[@class="hours flex"]/div[@class="col flex"]')
        for hours_column in hours_columns:
            day_names = hours_column.xpath('.//div[@class="day flex"]/p/span/text()').getall()
            times = hours_column.xpath('.//div[@class="time flex"]/p/span/text()').getall()
            days = zip(day_names, times)
            for day in days:
                times = day[1].upper().replace("OPEN 24 HOURS", "12:00AM-11:59PM")
                if "CLOSED" in times:
                    continue
                open_time, close_time = times.split("-", 1)
                if ":" not in open_time:
                    open_time = open_time.replace("AM", ":00AM").replace("PM", ":00PM")
                if ":" not in close_time:
                    close_time = close_time.replace("AM", ":00AM").replace("PM", ":00PM")
                item["opening_hours"].add_range(day[0], open_time, close_time, "%I:%M%p")

        if m := re.search(r"\w\w\.lat=(-?\d+\.\d+);\w\w\.lng=(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()
        yield item
