from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class CobsBreadSpider(SitemapSpider):
    name = "cobs_bread"
    item_attributes = {"brand": "COBS Bread", "brand_wikidata": "Q116771375"}
    allowed_domains = ["www.cobsbread.com"]
    sitemap_urls = ["https://www.cobsbread.com/bakery-sitemap.xml"]
    sitemap_rules = [(r"/local-bakery/", "parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//h1[contains(@class, "bakery__subtitle")]/text()').get().strip(),
            "website": response.url,
        }
        lat_raw = response.xpath("//@data-lat").get()
        if lat_raw is None or len(lat_raw) == 0:
            return
        else:
            properties["lat"] = lat_raw
        lon_raw = response.xpath("//@data-lng").get()
        if lon_raw is None or len(lon_raw) == 0:
            return
        else:
            properties["lon"] = lon_raw
        addr_raw = response.xpath("//@data-address").get()
        if addr_raw is not None and len(addr_raw) > 0:
            properties["addr_full"] = addr_raw
        phone_raw = response.xpath('//a[contains(@class, "single-bakery__phone")]/@href').get()
        if phone_raw is not None and len(phone_raw) > 0:
            properties["phone"] = phone_raw.split("tel:", 1)[1]
        oh = OpeningHours()
        hours_raw = response.xpath(
            '//div[contains(@class, "bakery-hours")]/dl[contains(@class, "bakery-hours__day")]/*/text()'
        ).getall()
        hours_split = (
            " ".join(hours_raw)
            .replace(" am", "AM")
            .replace(" AM", "AM")
            .replace(" pm", "PM")
            .replace(" PM", "PM")
            .replace("-", " ")
            .split()
        )
        if len(hours_split) == 21:
            hours_split = [hours_split[n : n + 3] for n in range(0, len(hours_split), 3)]
            for day in hours_split:
                oh.add_range(day[0], day[1], day[2], "%I:%M%p")
            properties["opening_hours"] = oh.as_opening_hours()
        yield Feature(**properties)
