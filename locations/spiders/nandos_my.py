import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosMYSpider(SitemapSpider):
    name = "nandos_my"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    allowed_domains = ["nandos.com.my"]
    sitemap_urls = ["https://nandos.com.my/wp-sitemap.xml"]
    sitemap_follow = ["restaurants"]
    sitemap_rules = [("/restaurants/", "parse_store")]

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        restaurant_data = response.xpath(
            '//div[@class="restaurant-details-wrapper"]/script[contains(text(),"var restaurant")]'
        ).extract_first()
        lat, lon = re.search(r"var restaurant = {.*: (.*), .*: (.*)}", restaurant_data).groups()

        properties = {
            "ref": ref,
            "country": "MY",
            "lat": lat,
            "lon": lon,
            "website": response.url,
        }

        yield Feature(**properties)
