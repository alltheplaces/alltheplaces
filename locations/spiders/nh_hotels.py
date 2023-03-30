from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

class NHHotelsSpider(SitemapSpider):
    name = "nh_hotels"
    item_attributes = {"brand": "NH Hotel Group", "brand_wikidata": "Q1604631"}
    allowed_domains = ["nh-hotels.com"]
    sitemap_urls = ["https://www.nh-hotels.com/hotels-sitemap.xml"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        name = response.xpath('//*[@class="box m-hotel-detail"]//*[@class="h2"]/text()').get()
        addr_full = response.xpath('//*[@class="box m-hotel-detail"]//*[@class="link-icon"]/text()').get().strip()
        phone = response.xpath('//*[@class="box m-hotel-detail"]//*[@class="dynamicTelephone link-primary track-phoneNumberGA4"]/text()').get()
        email = response.xpath('//*[@class="box m-hotel-detail"]//*[@class="link-primary"]/text()')
        return 0
