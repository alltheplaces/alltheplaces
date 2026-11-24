import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcPHSpider(SitemapSpider):
    name = "kfc_ph"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["www.kfc.com.ph"]
    sitemap_urls = ["https://www.kfc.com.ph/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("KFC ")
        item["addr_full"] = (
            response.xpath("//p[normalize-space()='Address']/following-sibling::p[1]//text()").get().strip()
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        item["ref"] = item["website"] = response.url
        if lat_lon := re.search(
            r"\\\"latitude\\\":(\d+\.\d+),\\\"longitude\\\":(\d+\.\d+)",
            response.xpath('//*[contains(text(), "coordinates")]/text()').get(),
        ):
            item["lat"], item["lon"] = lat_lon.groups()
        try:
            oh = OpeningHours()
            for day_time in response.xpath('//*[@class="md:hidden flex flex-col"]/div'):
                day = day_time.xpath("./div[1]//text()").get()
                time = day_time.xpath("./div[2]//text()").get()
                if time in ["Closed All Day"]:
                    continue
                if time == "Open All Day":
                    oh.add_range(day=day, open_time="00:00", close_time="23:59")
                else:
                    open_time, close_time = time.split("-")
                    oh.add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M%p"
                    )
                item["opening_hours"] = oh
        except:
            pass

        yield item
