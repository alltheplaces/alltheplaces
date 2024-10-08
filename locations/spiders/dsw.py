import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class DswSpider(SitemapSpider):
    name = "dsw"
    item_attributes = {"brand": "Designer Shoe Warehouse", "brand_wikidata": "Q5206207"}
    allowed_domains = [
        "stores.dsw.com",
        "stores.dsw.ca",
    ]
    sitemap_urls = [
        "https://stores.dsw.com/sitemap.xml",
        "https://stores.dsw.ca/sitemap.xml",
    ]
    sitemap_rules = [
        (
            r"https:\/\/stores\.dsw\.com\/usa\/(\w{2})\/([-\w]+)\/([-\w']+)\.html$",
            "parse_store",
        ),
        (r"https:\/\/stores\.dsw\.ca\/(\w{2})\/([-\w]+)\/([-\w]+)$", "parse_store"),
    ]

    def parse_store(self, response):
        oh = OpeningHours()

        phone = (
            response.xpath('normalize-space(//span[@id="telephone"]/text())').extract_first()
            or response.xpath('normalize-space(//div[@id="phone-main"]/text())').extract_first()
        )
        opening_hrs = (
            response.xpath('//script[@class="js-hours-config"]/text()').extract_first()
            or response.xpath('//span[@class="c-location-hours-today js-location-hours"]/@data-days').extract_first()
        )
        hrs = json.loads(opening_hrs)
        if isinstance(hrs, dict):
            hrs = hrs.get("hours")

        for day in hrs:
            for interval in day.get("intervals"):
                ot = interval.get("start")
                ct = interval.get("end")
                oh.add_range(day.get("day").title()[:2], str(ot), str(ct), time_format="%H%M")

        properties = {
            "street_address": response.xpath('//span[@class="c-address-street-1"]/text()').extract_first(),
            "phone": phone,
            "city": response.xpath('//span[@class="c-address-city"]/text()').extract_first(),
            "state": response.xpath('//abbr[@class="c-address-state"]/text()').extract_first(),
            "postcode": response.xpath('//span[@class="c-address-postal-code"]/text()').extract_first(),
            "ref": response.xpath('//span[@class="LocationName-geo"]/text()').extract_first(),
            "website": response.url,
            "lat": response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            "lon": response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
            "opening_hours": oh.as_opening_hours(),
        }
        if "stores.dsw.com" in response.url:
            properties["country"] = "US"
        elif "stores.dsw.ca" in response.url:
            properties["country"] = "CA"

        yield Feature(**properties)
