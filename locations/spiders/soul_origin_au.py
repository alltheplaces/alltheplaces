from scrapy import Selector, Spider

from locations.items import Feature


class SoulOriginAUSpider(Spider):
    name = "soul_origin_au"
    item_attributes = {"brand": "Soul Origin", "brand_wikidata": "Q110473093"}
    start_urls = ["https://www.soulorigin.com.au/wp-admin/admin-ajax.php?action=get_store_location"]

    def parse(self, response, **kwargs):
        location_list = Selector(text=response.json()["location_list"])
        for location in response.json()["location_markers"]:
            item = Feature()
            item["ref"] = location["store_id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["name"] = location["title"]

            info = location_list.xpath(f'//li[@id="li_{location["store_id"]}"]')
            item["addr_full"] = info.xpath(".//p/text()").get()
            item["website"] = info.xpath('.//a[contains(text(), "store details")]/@href').get()

            yield item
