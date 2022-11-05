import re

from scrapy.spiders import SitemapSpider

from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class GraetersSpider(SitemapSpider):
    name = "graeters"
    item_attributes = {
        "brand": "Graeter's",
        "brand_wikidata": "Q5592430",
    }
    allowed_domains = ["www.graeters.com"]
    sitemap_urls = ["https://www.graeters.com/sitemap.xml"]
    sitemap_rules = [(r"retail-stores/", "parse")]

    def parse(self, response):
        map_url = response.xpath('//a/@href[contains(.,"maps/dir")]').get()
        (lat, lon) = url_to_coords(map_url)
        hours = self.parse_hours(response.xpath('//*[starts-with(text(),"Mon ")]/..'))

        item = {
            "ref": response.url,
            "website": response.url,
            "lat": lat,
            "lon": lon,
            "addr_full": response.css("address::text").get(),
            "phone": response.css("a.location-phone::text").get(),
            "opening_hours": hours,
        }
        yield GeojsonPointItem(**item)

    def parse_hours(self, ul):
        opening_hours = OpeningHours()
        for txt in ul.xpath(".//li/text()").extract():
            day, interval = txt.split(" ", 1)
            if interval == "CLOSED":
                continue
            open_time, close_time = re.split(" ?- ?", interval, 1)
            opening_hours.add_range(day[:2], open_time, close_time, "%I:%M%p")
        return opening_hours.as_opening_hours()
