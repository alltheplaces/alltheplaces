from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule, DetectionResponseRule
from locations.dict_parser import DictParser
from locations.items import Feature

# Official website for Storemapper:
# https://storemapper.com/
#
# To use this store finder, specify a company_id as a string. This company_id
# if usually a single integer, but can sometimes also have a suffix (separated
# with a hyphen) that contains word characters (e.g. a-zA-Z0-9 observed to be
# used if a suffix is included).
#
# If clean ups or additional field extraction is required from the
# source data, override the parse_item function. Two parameters are
# passed, item (an ATP "Feature" class) and location (a dict which
# is returned from the store locator JSON response for a particular
# location).


class StoremapperSpider(Spider, AutomaticSpiderGenerator):
    """
    Storemapper (https://www.storemapper.com/) is an emedded map based store locator.

    API docs are available via https://help.storemapper.com/category/4313-advanced-settings-and-customisation

    To use, specify:
      - `company_id`: mandatory parameter
    """

    dataset_attributes = {"source": "api", "api": "storemapper.com"}
    company_id: str = ""
    custom_settings = {"ROBOTSTXT_OBEY": False}
    detection_rules = [
        DetectionRequestRule(
            url=r"^https:\/\/storemapper-herokuapp-com\.global\.ssl\.fastly\.net\/api\/users\/(?P<company_id>\d+(?:-\w+)?)\/stores\.js(?:\?|$)"
        ),
        DetectionResponseRule(js_objects={"company_id": r"window.Storemapper.companyId"}),
        DetectionResponseRule(xpaths={"company_id": r"//script/@data-storemapper-id"}),
    ]

    def start_requests(self):
        yield JsonRequest(
            url=f"https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/{self.company_id}/stores.js"
        )

    def parse(self, response: Response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict):
        yield item
