from urllib.parse import urljoin

from scrapy.http import JsonRequest, Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class KuveytTurkTRSpider(JSONBlobSpider):
    name = "kuveyt_turk_tr"
    item_attributes = {"brand": "Kuveyt Türk", "brand_wikidata": "Q6036058"}
    allowed_domains = ["kuveytturk.com.tr"]
    base_url = "https://www.kuveytturk.com.tr/"

    def start_requests(self):
        yield Request(urljoin(self.base_url, "/en/branches-and-atms"), callback=self.parse_branch_page)

    def parse_branch_page(self, response, **kwargs):
        # "ltst" to get province/city list, e.g. https://www.kuveytturk.com.tr/ck0d84?CEBBF620EBF992ADBA5A8EAB442F0483
        province_endpoint = response.xpath('//script[contains(text(), "addresses")]/text()').re_first(r'"ltst":"(.+?)"')

        # "ltssrt" to get district list from province, e.g. https://www.kuveytturk.com.tr/ck0d84?C5E80A141690211D3BDAE678996E2D9E&p1=42
        district_endpoint = response.xpath('//script[contains(text(), "addresses")]/text()').re_first(
            r'"ltssrt":"(.+?)"'
        )

        # "bnh" to get locations, e.g. https://www.kuveytturk.com.tr/ck0d84?D473E30CFFF82E38CBCEB43A6607CBAF&p5=42&p1%5B%5D=Normal&p1%5B%5D=Atm&p1%5B%5D=Xtm&p13=SEL%C3%87UKLU
        branch_endpoint = response.xpath('//script[contains(text(), "addresses")]/text()').re_first(r'"bnh":"(.+?)"')

        yield JsonRequest(
            urljoin(self.base_url, province_endpoint),
            callback=self.fetch_provinces,
            meta={"district_endpoint": district_endpoint, "branch_endpoint": branch_endpoint},
        )

    def fetch_provinces(self, response):
        for province in response.json():
            yield JsonRequest(
                urljoin(self.base_url, response.meta["district_endpoint"] + "&p1=" + str(province["Id"])),
                callback=self.fetch_districts,
                meta={"province_id": province["Id"], "branch_endpoint": response.meta["branch_endpoint"]},
            )

    def fetch_districts(self, response):
        for district in response.json():
            yield JsonRequest(
                urljoin(
                    self.base_url,
                    response.meta["branch_endpoint"]
                    + "&p5="
                    + str(response.meta["province_id"])
                    + "&p1[]=Normal&p1[]=Atm&p1[]=Xtm&p13="
                    + district["Name"],
                ),
                callback=self.parse,
            )

    def post_process_item(self, item, response, location):
        # Id is not unique across items, it appears to refer to a physical location, so a branch and two ATMs in one place all have the same Id
        item["ref"] = f"{location.get('Id')}-{location.get('Name').replace(' ', '_')}"

        if location["Type"] == 1:
            apply_category(Categories.BANK, item)
            # Unhandled: "IsForeignAccountOpening"
        elif location["Type"] in [2, 3]:  # 2: ATM, 3: XTM (special type of ATM)
            apply_category(Categories.ATM, item)
            apply_yes_no("currency:USD", item, location["IsDollarDispensible"], False)
            apply_yes_no(Extras.CASH_OUT, item, location["IsCashWithDrawal"], False)
            apply_yes_no(Extras.WHEELCHAIR, item, location["IsHandicapped"], False)
            apply_yes_no("speech_output", item, location["IsVoiceMenuActive"], False)
            # Unhandled: IsGoldDispensible, "IsLobi", "IsExchange"
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_type/{location['Type']}")

        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        item["state"] = location["District"]["City"]["Name"]
        item["city"] = location["District"]["Name"]

        yield item
