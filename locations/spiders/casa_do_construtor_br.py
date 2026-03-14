from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature, SocialMedia, set_social_media


class CasaDoConstrutorBRSpider(SitemapSpider):
    name = "casa_do_construtor_br"
    item_attributes = {"brand": "Casa do Construtor", "brand_wikidata": "Q118672258"}
    sitemap_urls = ["https://casadoconstrutor.com.br/sitemap.xml"]
    sitemap_rules = [(r"/loja/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.xpath('//*[@id="store-cookie-lojaId"]/text()').get()
        item["website"] = response.url
        item["street_address"] = response.xpath('//*[@id="store-cookie-address"]/text()').get()
        item["branch"] = response.xpath('//*[@id="store-cookie-title"]/text()').get()
        item["phone"] = response.xpath('//*[@id="store-cookie-phone"]/text()').get()
        item["email"] = response.xpath('//*[@id="store-cookie-email"]/text()').get()

        if whatsapp := response.xpath('//*[@id="store-cookie-whatsapp"]/text()').get():
            set_social_media(item, SocialMedia.WHATSAPP, whatsapp)

        # coordinates are not available for all locations
        if map_url := response.xpath("//@data-maps-url").get():
            item["lat"], item["lon"] = url_to_coords(map_url)

        apply_category(Categories.SHOP_TOOL_HIRE, item)

        yield item
