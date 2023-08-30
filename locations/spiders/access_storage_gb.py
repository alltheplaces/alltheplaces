from scrapy import Spider

from locations.dict_parser import DictParser


class AccessStorageGBSpider(Spider):
    name = "access_storage_gb"
    item_attributes = {"brand": "Access", "brand_wikidata": "Q122022507"}
    start_urls = ["https://www.accessstorage.com/accessapi/stores/getallstores"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["Information"].update(location["Location"])
            location["Information"]["street_address"] = location["Information"].pop("Address")
            item = DictParser.parse(location["Information"])
            item["extras"]["branch"] = item.pop("name", None)

            item["website"] = location["Information"]["Link"]
            item["image"] = location["Information"]["Image"]

            yield item
