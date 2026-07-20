from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category, Categories
from locations.google_url import extract_google_position
from locations.items import Feature

# Malformed Microdata


class MilenceSpider(SitemapSpider):
    name = "milence"
    item_attributes = {"brand": "Milence", "brand_wikidata": "Q131904416"}
    sitemap_urls = ["https://milence.com/location-sitemap.xml"]
    sitemap_rules = [("com/location/", "parse")]

    def parse(self, response: TextResponse, **kwargs):
        item = Feature()
        item["ref"] = response.url.rsplit("/", 2)[1]
        item["website"] = response.url
        item["image"] = response.xpath('//div[@class="m-location-header__image"]//img/@src').get()
        item["branch"] = response.xpath('//div[@class="m-location-header__title"]/h1/text()').get()
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["city"] = response.xpath('//*[@itemprop="addressLocality"]/text()').get()
        item["country"] = response.xpath('//div[@class="m-location-header__country"]/text()').get()

        apply_category(Categories.CHARGING_STATION, item)
        extract_google_position(item, response)

        yield item
