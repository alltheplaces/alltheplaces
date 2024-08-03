from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.user_agents import CHROME_LATEST


class BangkokBankTHSpider(scrapy.Spider):
    name = "bangkok_bank_th"
    allowed_domains = ["www.bangkokbank.com"]
    item_attributes = {"brand_wikidata": "Q806483"}
    user_agent = CHROME_LATEST
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Ocp-Apim-Subscription-Key": "7d1b09abe2ea413cbf95b2d99782ed37",
            "X-Requested-With": "XMLHttpRequest",
        },
        "ROBOTSTXT_OBEY": False,
    }
    base_url = "https://www.bangkokbank.com/api/locationsearchservice/"

    def start_requests(self):
        yield JsonRequest(urljoin(self.base_url, "GetProvinceTh"), callback=self.parse_thailand_province)
        yield JsonRequest(urljoin(self.base_url, "GetCountryTh"), callback=self.parse_international)

    def parse_thailand_province(self, response):
        url_template = urljoin(self.base_url, "SearchThaiLandThWithLocation/{}/0/13.72643339/100.5303671/{}")
        for province in response.json():
            yield JsonRequest(url_template.format(province["Province"], "BRC"), callback=self.parse)
            yield JsonRequest(url_template.format(province["Province"], "ATM"), callback=self.parse)

    def parse_international(self, response):
        url_template = urljoin(self.base_url, "SearchInternationalTh/{}/0")
        for country in response.json():
            yield JsonRequest(url_template.format(country["Country"]), callback=self.parse)

    def parse(self, response):
        # TODO: parse hours
        for poi in response.json():
            item = DictParser.parse(poi)
            item["ref"] = f"{poi['BranchNo']}-{poi['Country']}"
            item["country"] = "TH" if poi["Country"] == "ประเทศไทย" else poi["Country"]
            item["branch"] = poi["BranchName"]
            if poi.get("Branch") == "x" or poi.get("InternationalBranch") == "x":
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, poi.get("ATM") == "x")
            else:
                apply_category(Categories.ATM, item)
            yield item
