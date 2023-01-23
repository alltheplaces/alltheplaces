import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class ShakeShackSpider(scrapy.spiders.SitemapSpider):
    name = "shake_shack"
    download_delay = 2.0
    item_attributes = {"brand": "Shake Shack", "brand_wikidata": "Q1058722"}
    allowed_domains = ["shakeshack.com"]
    sitemap_urls = [
        "https://shakeshack.com/sitemap.xml",
    ]
    sitemap_rules = [(r"/location/", "parse")]

    def parse(self, response):
        addr_container = response.css(".field--name-field-address-line-1").xpath("..")
        addr_text = addr_container.xpath("./div/text()|./text()").extract()
        # Site contains addresses from various countries completely unstructured,
        # as well as ad-hoc textual locations.
        addr_full = "; ".join(filter(None, (s.strip() for s in addr_text)))

        hours_text = response.xpath('//h3[text()="Hours"]/..//div/text()').extract()
        hours_text = list(filter(None, (s.strip() for s in hours_text)))
        oh = OpeningHours()
        for hours in hours_text:
            day, interval = hours.split(": ")
            open_time, close_time = interval.split(" \u2013 ")
            oh.add_range(day[:2], open_time, close_time, "%I:%M%p")

        properties = {
            "ref": response.url.split("/")[-1],
            "website": response.url,
            "lat": response.xpath("//@data-lat").get(),
            "lon": response.xpath("//@data-lng").get(),
            "name": response.xpath('//meta[@property="og:title"]/@content').get(),
            "opening_hours": oh.as_opening_hours(),
            "phone": response.css(".field--name-field-phone-number ::text").get(),
            "addr_full": addr_full,
        }
        yield Feature(**properties)
