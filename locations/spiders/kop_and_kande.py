import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class KopAndKandeSpider(SitemapSpider):
    name = "kop_and_kande"
    item_attributes = {"brand": "Kop & Kande", "brand_wikidata": "Q124005159"}
    sitemap_urls = ["https://www.kop-kande.dk/sitemap/content"]
    sitemap_rules = [(r"/find-butik/.+", "parse")]

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(
            response.xpath('//script[@type="application/json"]/text()').get().replace("&q;", '"')
        )
        store = data["stateCmsPage"]["properties"]
        store["street_address"] = store.pop("address")
        item = DictParser.parse(store)
        item["name"] = data["stateCmsPage"]["name"].replace("&a;", "&")
        item["website"] = response.url
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
