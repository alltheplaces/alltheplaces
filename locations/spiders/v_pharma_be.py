from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class VPharmaBESpider(SitemapSpider):
    name = "v_pharma_be"
    item_attributes = {"name": "VPharma", "brand": "VPharma", "brand_wikidata": "Q123363458"}
    sitemap_urls = ["https://www.vpharma.be/pharmacy-sitemap.xml"]
    sitemap_rules = [
        (r"https://www\.vpharma\.be/pharmacies/\d+-gmedi-.+", "parse_equipment_supplier"),
        (r"https://www\.vpharma\.be/pharmacies/\d+-(?!comptoir).+", "parse_pharmacy"),
    ]

    def parse_equipment_supplier(self, response, **kwargs):
        for store in response.xpath('//*[contains(@id,"coordonnesMag")]'):
            item = Feature()
            item["ref"] = store.xpath("./@id").get()
            item["website"] = response.url
            item["branch"] = store.xpath("./p[1]/strong/text()").get()
            item["addr_full"] = merge_address_lines(store.xpath("./p[1]/text()").getall())
            item["phone"] = store.xpath('./a[contains(@href, "tel:")]/@href').get()
            item["lat"], item["lon"] = url_to_coords(store.xpath('./a[contains(@href, "google")]/@href').get())
            apply_category(Categories.SHOP_MEDICAL_SUPPLY, item)
            yield item

    def parse_pharmacy(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//meta[@property="og:title"]/@content').get().split(" - VPharma")[0]
        address = response.xpath('//*[contains(@href,"google.com/maps")]')
        item["addr_full"] = merge_address_lines(address.xpath("./text()").getall())
        item["phone"] = address.xpath("./parent::p/text()").get()
        apply_category(Categories.PHARMACY, item)
        yield item
