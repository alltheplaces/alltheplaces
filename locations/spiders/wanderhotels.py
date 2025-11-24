from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class WanderhotelsSpider(SitemapSpider):
    name = "wanderhotels"
    item_attributes = {"brand": "Wanderhotels", "brand_wikidata": "Q123436959"}
    sitemap_urls = ["https://www.wanderhotels.com/en/hotel-sitemap.xml"]
    sitemap_rules = [(r"https://www\.wanderhotels\.com/en/hotel/.+", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["extras"]["brand:website"] = response.url
        item["branch"] = response.xpath("//@data-hotelname").get().replace("Wanderhotel ", "")
        item["addr_full"] = merge_address_lines(response.xpath('//*[@class="singleHotel__street"]/text()').getall())
        item["country"] = response.xpath('//*[@class="singleHotel__region"]/span[1]/text()').get()
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/text()').get()
        item["email"] = response.xpath('//a[contains(@href, "mailto")]/text()').get()
        item["extras"]["fax"] = merge_address_lines(response.xpath('//*[contains(@class, "fax")]/text()').getall())
        item["website"] = response.xpath('//a[contains(@id, "hotelWebsite")]/@href').get()
        apply_category(Categories.HOTEL, item)
        yield item
