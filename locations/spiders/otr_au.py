from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class OtrAUSpider(SitemapSpider):
    name = "otr_au"
    item_attributes = {"brand": "OTR", "brand_wikidata": "Q116394019"}
    sitemap_urls = ["https://www.otr.com.au/robots.txt"]
    sitemap_rules = [("/location/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//title/text()").get().removeprefix("OTR ").removesuffix(" - OTR")
        item["street_address"] = response.xpath("//iframe/@title").get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        extract_google_position(item, response)

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
