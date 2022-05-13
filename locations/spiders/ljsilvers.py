# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class LjsilversSpider(SitemapSpider):
    name = "ljsilvers"
    item_attributes = {"brand": "Long John Silver's", "brand_wikidata": "Q1535221"}
    allowed_domains = ["ljsilvers.com"]

    sitemap_urls = ["https://locations.ljsilvers.com/robots.txt"]
    sitemap_rules = [(r"^https://locations.ljsilvers.com/.*/.*/.*$", "parse")]

    def parse(self, response):
        main = response.xpath("//main")
        address = main.css("[itemprop=address]")

        opening_hours = OpeningHours()
        for row in response.xpath('//*[@itemprop="openingHours"]/@content').extract():
            day, interval = row.split(" ", 1)
            if interval == "Closed":
                continue
            open_time, close_time = interval.split("-")
            opening_hours.add_range(day, open_time, close_time)

        properties = {
            "ref": main.attrib["itemid"],
            "website": response.url,
            "name": response.css("span#location-name ::text").get(),
            "lat": response.css("[itemprop=latitude]").attrib["content"],
            "lon": response.css("[itemprop=longitude]").attrib["content"],
            "street_address": address.css("[itemprop=streetAddress]").attrib["content"],
            "city": address.css(".Address-city ::text").get(),
            "state": address.css("[itemprop=addressRegion] ::text").get(),
            "phone": response.css("[itemprop=telephone]::text").get(),
            "opening_hours": opening_hours.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
