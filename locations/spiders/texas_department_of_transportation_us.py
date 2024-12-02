from typing import Iterable
from urllib.parse import quote_plus

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TexasDepartmentOfTransportationUSSpider(Spider):
    name = "texas_department_of_transportation_us"
    item_attributes = {"operator": "Texas Department of Transportation", "operator_wikidata": "Q568743"}
    allowed_domains = ["its.txdot.gov"]
    start_urls = ["https://its.txdot.gov/its"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response) -> Iterable[JsonRequest]:
        district_data = response.xpath('//script[contains(text(), "mainViewModel.initialize(")]/text()').get().split("mainViewModel.initialize(", 1)[1].split(");", 1)[0]
        districts = parse_js_object(district_data)["districts"]
        for district in districts:
            yield JsonRequest(url="https://its.txdot.gov/its/DistrictIts/GetCctvStatusListByDistrict?districtCode={}".format(district["code"]), callback=self.parse_cameras)

    def parse_cameras(self, response: Response) -> Iterable[Feature]:
        for roadway, camera_list in response.json()["roadwayCctvStatuses"].items():
            for camera in camera_list:
                if camera["statusDescription"] != "Device Online":
                    # Camera disabled/unavailable and should be ignored.
                    continue
                properties = {
                    "ref": camera["icd_Id"],
                    "name": camera["name"],
                    "lat": camera["latitude"],
                    "lon": camera["longitude"],
                }
                apply_category(Categories.SURVEILLANCE_CAMERA, properties)
                properties["extras"]["contact:webcam"] = "https://its.txdot.gov/its/DistrictIts/GetCctvSnapshotByIcdId?icdId={}&districtCode={}".format(quote_plus(properties["ref"]), response.url.split("districtCode=", 1)[1])
                yield Feature(**properties)

