from typing import AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.big_c_th import BigCTHSpider
from locations.spiders.lotuss_th import LotussTHSpider
from locations.spiders.makro_th import MakroTHSpider
from locations.spiders.ptt_th import PttTHSpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.user_agents import CHROME_LATEST


class BangkokBankTHSpider(Spider):
    name = "bangkok_bank_th"
    allowed_domains = ["www.bangkokbank.com"]
    item_attributes = {"brand_wikidata": "Q806483"}
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Ocp-Apim-Subscription-Key": "7d1b09abe2ea413cbf95b2d99782ed37",
            "X-Requested-With": "XMLHttpRequest",
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": CHROME_LATEST,
    }
    base_url = "https://www.bangkokbank.com/api/locationsearchservice/"

    # Located_in wikidata mapping for ATMs in retail stores
    # Branch names contain Thai and/or English retail brand names
    LOCATED_IN_MAPPINGS = [
        (["7-11", "7-ELEVEN"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
        (["โลตัส", "LOTUS"], {"brand": LotussTHSpider.LOTUSS[0], "brand_wikidata": LotussTHSpider.LOTUSS[1]}),
        (["บิ๊กซี", "BIG C"], BigCTHSpider.item_attributes),
        (["ปตท", "PTT"], PttTHSpider.item_attributes),
        (["แม็คโคร", "MAKRO"], MakroTHSpider.item_attributes),
        (["บางจาก", "BANGCHAK"], {"brand": "Bangchak", "brand_wikidata": "Q6579719"}),
        (["ท็อปส์", "TOPS"], {"brand": "Tops", "brand_wikidata": "Q7825140"}),
    ]

    async def start(self) -> AsyncIterator[JsonRequest]:
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
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    item.get("branch", ""), self.LOCATED_IN_MAPPINGS, self
                )
            yield item
