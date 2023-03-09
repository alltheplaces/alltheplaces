from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class ZambreroSpider(SitemapSpider):
    name = "zambrero"
    item_attributes = {"brand": "Zambrero", "brand_wikidata": "Q18636431"}
    allowed_domains = [
        "www.zambrero.com.au",
        "www.zambrero.co.nz",
        "www.zambrero.ie",
        "www.zambrero.co.uk",
        "www.zambrero.com",
    ]
    sitemap_urls = [
        "https://www.zambrero.com.au/sitemap.xml",
        "https://www.zambrero.co.nz/sitemap.xml",
        "https://www.zambrero.ie/sitemap.xml",
        "https://www.zambrero.co.uk/sitemap.xml",
        "https://www.zambrero.com/sitemap.xml",
    ]
    sitemap_rules = [(r"\/locations\/[^\/]+$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False} # robots.txt returns a HTTP 404 page that Scrapy tries to parse

    def parse(self, response):
        properties = {
            "ref": response.xpath('//div[contains(@class, "window")]/@data-location-id').get(),
            "name": " ".join(response.xpath('//div[contains(@class, "window")]/h4/text()').get().split()),
            "lat": response.xpath('//span[contains(@class, "distance")]/@data-lat').get(),
            "lon": response.xpath('//span[contains(@class, "distance")]/@data-lng').get(),
            "addr_full": " ".join(response.xpath('//span[contains(@class, "address")]/text()').get().split()),
            "phone": response.xpath('//a[contains(@class, "phone")]/@href').get().replace("tel:", ""),
            "email": response.xpath('//a[contains(@href, "mailto:")]/@href').get().replace("mailto:", ""),
            "website": response.url,
        }
        if properties["phone"] == "0":
            properties.pop("phone")

        oh = OpeningHours()
        hours_raw = " ".join((" ".join(response.xpath('//div[contains(@class, "hours-item")]/span/text()').getall())).split()).replace(" : ", " ").replace(" - ", " ").replace("a.m.", "AM").replace("p.m.", "PM").split()
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if "AM" in day[1].upper() or "PM" in day[1].upper() or "AM" in day[2].upper() or "PM" in day[2].upper():
                time_format = "%I:%M%p"
            else:
                time_format = "%H:%M"
            oh.add_range(day[0], day[1].upper(), day[2].upper(), time_format)
        properties["opening_hours"] = oh.as_opening_hours()

        # Some store names and URLs contain "Opening Soon" but numerous of
        # these are already open and the URL hasn't been changed. A more
        # reliable way of knowing a store is not yet open is that it has
        # no opening hours specified.
        if not properties["opening_hours"]:
            return

        yield Feature(**properties)
