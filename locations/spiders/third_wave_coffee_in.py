from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class ThirdWaveCoffeeINSpider(SitemapSpider):
    name = "third_wave_coffee_in"
    item_attributes = {"brand": "Third Wave Coffee Roasters", "brand_wikidata": "Q7785004"}
    sitemap_urls = ["https://cafe.thirdwavecoffee.in/sitemaps/v1/google/index-10001.xml"]
    sitemap_follow = ["dealer"]
    sitemap_rules = [(r"https://cafe\.thirdwavecoffee\.in/coffee-cafe-[-\w]+/home$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["city"] = response.xpath('//li[contains(@class, "br-info-card-str-loc")]/span/text()').get()
        item["addr_full"] = response.xpath('//*[@id="cadrs"]/@value').get()
        item["phone"] = response.xpath('//*[@id="ctele"]/@value').get()
        item["email"] = response.xpath('//a[contains(@href, "mailto")]/@href').get().replace("mailto:", "")
        item["name"] = response.xpath('//*[@id="cname"]/@value').get()
        item["ref"] = item["website"] = response.url
        apply_category(Categories.COFFEE_SHOP, item)
        extract_google_position(item, response)
        yield item
