from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class OmniHotelsSpider(SitemapSpider):
    name = "omni_hotels"
    item_attributes = {"brand": "Omni Hotels", "brand_wikidata": "Q7090329", "extras": Categories.HOTEL.value}
    sitemap_urls = ["https://www.omnihotels.com/sitemap.xml"]
    sitemap_rules = [(r"/property-details$", "parse")]

    def parse(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//*[@class="hotelName"]/text()').get()
        item["addr_full"] = clean_address(
            response.xpath('//*[contains(@class, "plp-contact-link")]/text()').getall()[0:4]
        )
        item["phone"] = response.xpath('.//a[contains(@href, "tel_link:")]/text()').get()
        extract_google_position(item, response)
        yield item
