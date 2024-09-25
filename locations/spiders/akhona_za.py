from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class AkhonaZASpider(Spider):
    name = "akhona_za"
    start_urls = ["https://www.akhonafurn.co.za/furniture-stores"]
    item_attributes = {
        "brand": "Akhona",
        "brand_wikidata": "Q116620476",
        "nsi_id": "N/A",  # Because of the warehouse
    }

    def parse(self, response):
        for location in response.xpath('.//li[contains(@class, "dmGeoMLocItem")]'):
            item = Feature()
            item["ref"] = location.xpath("@geoid").get().strip()
            item["name"] = self.item_attributes["brand"]
            item["branch"] = location.xpath('.//span[@class="dmGeoMLocItemTitle"]/text()').get().strip()
            if item["branch"] == "Warehouse":
                apply_category(Categories.INDUSTRIAL_WAREHOUSE, item)
                item.pop("branch")
            else:
                apply_category(Categories.SHOP_FURNITURE, item)

            item["addr_full"] = location.xpath('.//span[@class="dmGeoMLocItemDetails"]/text()').get().strip()
            addr_lines = item["addr_full"].split(",")
            item["street_address"] = addr_lines[0].strip()
            try:
                int(addr_lines[-2])
                item["postcode"] = addr_lines[-2].strip()
            except ValueError:
                pass

            yield item
