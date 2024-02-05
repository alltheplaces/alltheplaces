import json
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MailBoxesEtcGBIESpider(Spider):
    name = "mail_boxes_etc_gb_ie"
    item_attributes = {"brand": "Mail Boxes Etc.", "brand_wikidata": "Q92922921"}
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    def start_requests(self):
        yield JsonRequest(
            "https://www.mbe.co.uk/Services/StoreLocationWebService.asmx/ShowAllStores",
            data={"userRegionCheckBoxValue": False},
        )

    def parse(self, response: Response, **kwargs):
        for location in json.loads(response.json()["d"]["StoreLocationResults"]):
            item = DictParser.parse(location)
            item["website"] = urljoin("https://www.mbe.co.uk", location["Directory"])
            apply_category(Categories.POST_OFFICE, item)
            yield item
