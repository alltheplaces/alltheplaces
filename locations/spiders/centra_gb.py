import html

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.centra_ie import CentraIESpider


class CentraGBSpider(Spider):
    name = "centra_gb"
    item_attributes = CentraIESpider.item_attributes
    start_urls = ["https://www.centra.co.uk/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = ", ".join(filter(None, [location.pop("address"), location["address2"]]))
            location["name"] = html.unescape(location.pop("store"))
            county = location.pop("country")
            if county not in ["Northen Ireland", "Northern Ireland", "United Kingdom"]:
                location["state"] = county
            item = DictParser.parse(location)

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
