from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class DruryHotelsUSSpider(SitemapSpider):
    name = "drury_hotels_us"
    item_attributes = {"brand": "Drury Inn & Suites", "brand_wikidata": "Q5309391"}
    allowed_domains = ["druryhotels.com"]
    sitemap_urls = ["https://www.druryhotels.com/sitemap.xml"]
    # Only match hotel detail pages (not city pages)
    sitemap_rules = [(r"/locations/[^/]+/[^/]+$", "parse")]

    def parse(self, response):
        item = Feature()
        item["website"] = response.url
        item["ref"] = response.url
        item["street_address"] = response.css('span[itemprop="streetAddress"]::text').get()
        item["city"] = response.css('span[itemprop="addressLocality"]::text').get()
        item["state"] = response.css('span[itemprop="addressRegion"]::text').get()
        item["postcode"] = response.css('span[itemprop="postalCode"]::text').get()
        item["phone"] = response.css('span[itemprop="telephone"] a::text').get()
        item["country"] = "US"
        item["image"] = response.css(".first ::attr(data-src)").get()
        extract_google_position(item, response)

        yield item
