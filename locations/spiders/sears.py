import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class SearsSpider(scrapy.spiders.SitemapSpider):
    name = "sears"
    item_attributes = {"brand": "Sears", "brand_wikidata": "Q6499202"}
    allowed_domains = ["www.sears.com"]
    sitemap_urls = ["https://www.sears.com/Sitemap.xml"]
    sitemap_rules = [
        (r"\d+\.html$", "parse"),
    ]
    download_delay = 0.3

    def parse(self, response):
        # Handle redirects to closed store page, majority are regular store detail pages
        if response.request.meta.get("redirect_urls") and "store-closed" in response.url:
            return
        oh = OpeningHours()
        for hours_li in response.css(".shc-store-hours")[0].css("li"):
            day, interval = hours_li.css("span::text").extract()
            open_time, close_time = interval.split(" - ")
            oh.add_range(day, open_time, close_time, "%I:%M %p")

        addr_txt = response.css(".shc-store-location__details--address")[0].css("::text").extract()
        street_address, city_postcode = list(filter(None, (s.strip() for s in addr_txt)))
        city, postcode = city_postcode.split(",  ")
        properties = {
            "ref": response.xpath("//@data-unit-number").get(),
            "name": response.xpath("//@data-store-title").get(),
            "lat": response.xpath("//@data-latitude").get(),
            "lon": response.xpath("//@data-longitude").get(),
            "street_address": street_address,
            "city": city,
            "postcode": postcode,
            "state": response.url.split("/")[-3],
            "website": response.url,
            "phone": response.css(".shc-store-location__details--tel::text").get(),
            "opening_hours": oh.as_opening_hours(),
        }
        if "Hometown" in properties["name"]:
            # See sears_hometown; ref should be shared
            # Address and coordinates are slightly off
            properties.update({"brand": "Sears Hometown", "brand_wikidata": "Q69926963"})
        elif "Mattress" in properties["name"]:
            # Likely stale; these are now american_freight
            # Refs are distinct
            properties.update({"brand": "Sears Outlet", "brand_wikidata": "Q20080412"})
        yield Feature(**properties)
