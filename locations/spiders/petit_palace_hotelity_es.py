from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PetitPalaceHotelityESSpider(CrawlSpider, StructuredDataSpider):
    name = "petit_palace_hotelity_es"
    item_attributes = {"brand": "Petit Palace Hotelity", "brand_wikidata": "Q125472094"}
    start_urls = ["https://www.petitpalace.com/es/hoteles/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/es/[a-z-]+/", restrict_xpaths='//*[@class="wrap-products-element"]'),
            callback="parse_sd",
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Petit Palace ", "")
        item["website"] = response.url
        apply_category(Categories.HOTEL, item)
        yield item
