from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class BigBoyUSSpider(SitemapSpider):
    name = "big_boy_us"
    item_attributes = {"brand": "Big Boy", "brand_wikidata": "Q4386779"}
    allowed_domains = ["www.bigboy.com"]
    sitemap_urls = ["https://www.bigboy.com/dynamic-location-sitemap.xml"]
    sitemap_rules = [(r"/location/big-boy", "parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath("//main/section/div[2]/div[3]/div[2]/h2/text()").get(default="").replace("®", ""),
            "addr_full": response.xpath("//main/section/div[2]/div[2]/div[4]/div[3]/p/a/text()").get(),
            "phone": response.xpath("//main/section/div[2]/div[2]/div[7]/div[3]/p/a/text()").get(),
            "website": response.url,
        }
        extract_google_position(properties, response)
        oh = OpeningHours()
        hours_raw = " ".join(
            (" ".join(response.xpath("//main/section/div[2]/div[2]/div[11]/div[3]/p/text()").getall())).split()
        )
        oh.add_ranges_from_string(hours_raw)
        properties["opening_hours"] = oh.as_opening_hours()
        yield Feature(**properties)
