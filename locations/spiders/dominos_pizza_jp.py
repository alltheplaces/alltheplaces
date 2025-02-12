import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaJPSpider(SitemapSpider):
    name = "dominos_pizza_jp"
    item_attributes = {
        "brand_wikidata": "Q839466",
        "country": "JP",
    }
    allowed_domains = ["dominos.jp"]
    sitemap_urls = [
        "https://www.dominos.jp/sitemap.aspx",
    ]
    sitemap_rules = [(r"/store", "parse_store")]
    user_agent = BROWSER_DEFAULT

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        properties = {
            "ref": ref,
            "name": response.xpath('normalize-space(//h1[@class="storetitle"][1]/text())').extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//span[@id="store-address-info"]/p/text()[4])'
            ).extract_first(),
            "postcode": re.search(
                r"([\d-]*)$",
                response.xpath('normalize-space(//div[@class="store-details-text"]/span/p/text()[2])').extract_first(),
            ).group(1),
            "lat": response.xpath('normalize-space(//input[@id="store-lat"]/@value)').extract_first(),
            "lon": response.xpath('normalize-space(//input[@id="store-lon"]/@value)').extract_first(),
            "phone": response.xpath('//div[@id="store-tel"]/a/text()').extract_first(),
            "website": response.url,
        }

        yield Feature(**properties)
