from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PetitPalaceHotelityESSpider(SitemapSpider):
    name = "petit_palace_hotelity_es"
    item_attributes = {"brand": "Petit Palace Hotelity", "brand_wikidata": "Q125472094"}
    sitemap_urls = ["https://www.petitpalace.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.petitpalace.com/es/hoteles/[^/]+/ubicacion/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath('//h2[@class="subtitle"]/text()').get()
        item["addr_full"] = merge_address_lines(
            response.xpath('//h4[normalize-space()="Dirección"]/following-sibling::*[1]//p//text()').getall()
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["website"] = item["ref"] = response.url
        yield item
