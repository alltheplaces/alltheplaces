from scrapy import Spider

from locations.dict_parser import DictParser


class BiopedCASpider(Spider):
    name = "bioped_ca"
    item_attributes = {"brand": "BioPed", "brand_wikidata": "Q123409898"}
    start_urls = ["https://www.bioped.com/wp-content/uploads/agile-store-locator/locator-data.json"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["extras"]["fax"] = location["fax"]
            item["website"] = response.urljoin(location["page_url"])

            yield item
