from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_TR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcTRSpider(SitemapSpider):
    name = "kfc_tr"
    item_attributes = KFC_SHARED_ATTRIBUTES
    sitemap_urls = ["https://kfcturkiye.com/robots.txt"]
    sitemap_rules = [("/restoran/", "parse")]
    requires_proxy = "TR"

    def parse(self, response: Response, **kwargs: Any):
        item = Feature()
        item["branch"] = response.xpath('//div[@class="location-info"]/h3/text()').extract_first()
        item["addr_full"] = response.xpath('//div[@class="location-info"]/p/text()').extract_first().replace("'", "")
        item["website"] = item["extras"]["website:tr"] = item["ref"] = response.url
        item["extras"]["website:en"] = response.xpath('//a[@class="language mobile-hidden"]/@href').get()
        wh = response.xpath('//div[@class="working-hours-info"]/div[@class="hours-item"]/text()').extract()
        opening_hours = OpeningHours()

        for ls in wh:
            day, times = ls.split("/", maxsplit=1)
            start_time, end_time = times.split("-", maxsplit=1)
            if day := sanitise_day(day, DAYS_TR):
                opening_hours.add_range(day, start_time.strip(), end_time.strip(), time_format="%H:%M")
        item["opening_hours"] = opening_hours
        yield item
