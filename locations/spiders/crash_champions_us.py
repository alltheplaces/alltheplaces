import re

from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class CrashChampionsUSSpider(SitemapSpider):
    name = "crash_champions_us"
    sitemap_urls = [
        "https://www.crashchampions.com/sitemap.xml",
    ]

    sitemap_rules = [(r"/locations/", "parse_store")]

    def parse_store(self, response):
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath("//*[@class='about-center__center']/text()").extract_first(),
            "addr_full": response.xpath("//*[@class='about-center__address']/text()").extract_first().strip(),
            "phone": response.xpath("//*[@class='about-center__phoneno']/a/text()").extract_first().strip(),
            "website": response.url,
        }

        item = Feature(**properties)
        item["opening_hours"] = OpeningHours()
        for day_range in response.xpath("//*[@class='about-center__timings']/p/text()").getall():
            item["opening_hours"].add_ranges_from_string(day_range)

        extract_google_position(item, response)
        yield item
