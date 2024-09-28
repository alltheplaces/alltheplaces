import scrapy

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class LoewsHotelsSpider(StructuredDataSpider):
    name = "loews_hotels"
    item_attributes = {"brand": "Loews Hotels", "brand_wikidata": "Q6666622", extras: Categories.HOTEL.values}
    allowed_domains = ["loewshotels.com"]
    start_urls = ("https://www.loewshotels.com/destinations",)
    search_for_twitter = False
    wanted_types = ["Hotel"]

    def parse(self, response):
        urls = response.xpath('//div[@class="buttons"]/a/@href').extract()
        for url in urls:
            if url.startswith("reservations.loewshotels.com"):
                pass
            elif "omni" in url:
                pass
            elif "hotel-1000" in url:
                pass
            elif "policy" in url:
                pass
            elif "mokara" in url:
                pass
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
