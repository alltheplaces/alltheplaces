from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class KiplingUSSpider(SitemapSpider):
    name = "kipling_us"
    item_attributes = {"brand": "Kipling", "brand_wikidata": "Q6414641"}
    sitemap_urls = ["https://locations.kipling.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.kipling.com/us/[^/]+/[^/]+/[^/]+$", "parse")]

    def parse(self, response: TextResponse, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath('//*[@property="business:contact_data:street_address"]/@content').get()
        item["city"] = response.xpath('//*[@property="business:contact_data:locality"]/@content').get()
        item["state"] = response.xpath('//*[@property="business:contact_data:region"]/@content').get()
        item["postcode"] = response.xpath('//*[@property="business:contact_data:postal_code"]/@content').get()
        item["phone"] = response.xpath('//*[@property="business:contact_data:phone_number"]/@content').get()
        item["lat"] = response.xpath('//*[@property="place:location:latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@property="place:location:longitude"]/@content').get()
        item["ref"] = item["website"] = response.url

        apply_category(Categories.SHOP_BAG, item)

        yield item
