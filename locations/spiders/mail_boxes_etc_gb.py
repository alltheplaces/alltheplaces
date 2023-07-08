import json

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class MailBoxesEtcGBSpider(Spider):
    name = "mail_boxes_etc_gb"
    item_attributes = {"brand": "Mail Boxes Etc.", "brand_wikidata": "Q92922921"}

    def start_requests(self):
        yield JsonRequest(
            "https://www.mbe.co.uk/Services/StoreLocationWebService.asmx/ShowAllStores",
            data={"userRegionCheckBoxValue": False},
        )

    def parse(self, response: Response, **kwargs):
        for location in json.loads(response.json()["d"]["StoreLocationResults"]):
            item = DictParser.parse(location)

            item["website"] = response.urljoin(location["Directory"])

            yield item
