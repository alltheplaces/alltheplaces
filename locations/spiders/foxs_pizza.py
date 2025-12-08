import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class FoxsPizzaSpider(SitemapSpider):
    name = "foxs_pizza"
    item_attributes = {"brand": "Fox's Pizza Den", "brand_wikidata": "Q5476498"}
    allowed_domains = ["foxspizza.com"]
    sitemap_urls = ["https://www.foxspizza.com/store-sitemap.xml"]
    oh_pattern = re.compile(r"(\w+):\s*(\d+:\d\d [AP]M) to (\d+:\d\d [AP]M)", re.IGNORECASE)

    def parse(self, response):
        lat, lng = map(float, re.search(r"LatLng\((.*),(.*)\),", response.text).groups())
        properties = {
            "lat": lat,
            "lon": lng,
            "ref": response.url,
            "website": response.url,
            "opening_hours": self.parse_opening_hours(response.xpath('//*[@class="timings_list"]//text()').getall()),
            "addr_full": response.xpath('//*[@class="loc_address"]/text()').get().replace("\xa0", " "),
            "phone": response.xpath('//*[@class="phone_no"]//text()').get(),
            "name": response.xpath("//title/text()").get(),
        }
        yield Feature(**properties)

    def parse_opening_hours(self, rules: [str]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if m := re.match(self.oh_pattern, rule):
                oh.add_range(m.group(1), m.group(2), m.group(3), time_format="%I:%M %p")
        return oh
