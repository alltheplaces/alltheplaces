import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class AuchanHUSpider(SitemapSpider):
    name = "auchan_hu"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}
    sitemap_urls = ["https://www.auchan.hu/sitemap.xml"]
    sitemap_rules = [
        (r"/aruhazak/auchan-", "parse_store"),
        (r"/benzinkutak/auchan-", "parse_gas_station"),
    ]

    def parse_store(self, response, **kwargs):
        location = chompjs.parse_js_object(response.xpath('//script[contains(text(), "shopsmap")]/text()').get())
        item = DictParser.parse(location[0])
        item["ref"] = item["website"] = response.url
        address_info = response.xpath('//*[contains(@class,"shopCard")]//p/text()').get()
        item["addr_full"], item["phone"] = (
            address_info.split("Központi szám:") if "Központi szám:" in address_info else (address_info, None)
        )
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item

    def parse_gas_station(self, response, **kwargs):
        # coordinates etc. in page's js_object belong to shops instead of gas station, hence ignored.
        if address := response.xpath('//*[contains(@class,"petrolAddress")]/text()').get():
            item = Feature()
            item["ref"] = item["website"] = response.url
            item["name"] = clean_address(response.xpath('//*[contains(@class,"selectedStation")]/text()').getall())
            item["addr_full"] = clean_address(address)
            item["nsi_id"] = "N/A"
            apply_category(Categories.FUEL_STATION, item)
            yield item
