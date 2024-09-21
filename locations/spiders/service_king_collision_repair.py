import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.google_url import extract_google_position


class ServiceKingCollisionRepairSpider(SitemapSpider):
    name = "service_king_collision_repair"
    # allowed_domains = ["serviceking.com"]
    sitemap_urls = [
        "https://www.crashchampions.com/sitemap.xml",
    ]

    sitemap_rules = [(r"/locations/", "parse_store")]

    def parse_store(self, response):
        info = response.xpath("//*[@class='about-center__address']/text()").extract_first()
        # city, state, postal = info.split(",")
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath("//*[@class='about-center__center']/text()").extract_first(),
            "addr_full": response.xpath("//*[@class='about-center__address']/text()").extract_first().strip(),
            # "city": city.strip(),
            # "state": state.strip(),
            # "postcode": postal.strip(),
            "country": "US",
            "phone": response.xpath("//*[@class='about-center__phoneno']/a/text()")
            .extract_first()
            .strip(),
            "website": response.url,
        }

        item = Feature(**properties)
        extract_google_position(item, response)
        yield item
