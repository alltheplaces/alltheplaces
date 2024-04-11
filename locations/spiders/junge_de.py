import json
import re

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours


class JungeDESpider(Spider):
    name = "junge_de"
    item_attributes = {"brand": "Junge", "brand_wikidata": "Q1561751"}
    start_urls = ["https://shop.jb.de/geschaeftefinder"]

    def details_request_body(self, branch_id):
        return json.dumps(
            dict(
                branchId=branch_id,
                responseType="addon",
            )
        )

    def parse(self, response: Response):
        branches = response.xpath("//store-finder-core").attrib[":branches"]
        branches = re.sub(r"\"branch(.+?)\"", r'"\g<1>"', branches, flags=re.DOTALL)
        for branch in parse_js_object(branches):
            branch["Address"]["streetAddress"] = branch["Address"].pop("street")
            internal_id = branch["Id"]
            branch["coordinates"], branch["Id"] = branch["Address"], branch["ERPId"]
            branch["phone"] = branch["Address"]["phone"]
            yield Request(
                "https://shop.jb.de/api/branch/details",
                method="POST",
                body=self.details_request_body(internal_id),
                headers={"Content-Type": "application/json"},
                meta=dict(item=DictParser.parse(branch)),
                callback=self.parse_detail,
            )

    def parse_detail(self, response: Response):
        opening_hours = OpeningHours()
        for rule in response.json()["branchOpeningHours"]:
            opening_hours.add_ranges_from_string(":".join([rule["weekdayLabel"], rule["timespan"]]), days=DAYS_DE)
        response.meta["item"]["opening_hours"] = opening_hours
        yield response.meta["item"]
