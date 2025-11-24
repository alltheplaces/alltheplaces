from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class IhHotelsITSpider(SitemapSpider):
    name = "ih_hotels_it"
    item_attributes = {"brand": "iH Hotel", "brand_wikidata": "Q126033607"}
    sitemap_urls = ["https://ih-hotels.com/page-sitemap.xml"]
    sitemap_rules = [(r"/city-hotel/(?!.*\bmilan\b)[^/]+/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@id="section-34-61"]//strong/text()').get().replace("\xa0", " ")
        item["addr_full"] = clean_address(response.xpath('//*[@id="section-34-61"]//p/text()[1]').get())
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/@href').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["ref"] = item["website"] = response.url
        if "APARTHOTEL" in item["branch"].upper():
            apply_category(Categories.TOURISM_APARTMENT, item)
            item["branch"] = item["branch"].replace("iH ApartHotels ", "")
        else:
            apply_category(Categories.HOTEL, item)
            item["branch"] = item["branch"].replace("iH Hotels ", "")
        yield item
