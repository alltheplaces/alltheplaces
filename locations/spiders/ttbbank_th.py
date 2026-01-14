from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.big_c_th import BigCTHSpider
from locations.spiders.cp_freshmart_th import CpFreshmartTHSpider
from locations.spiders.familymart_my import FamilymartMYSpider
from locations.spiders.lotuss_th import LotussTHSpider
from locations.spiders.makro_th import MakroTHSpider
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.spiders.ptt_th import PttTHSpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class TtbbankTHSpider(Spider):
    name = "ttbbank_th"
    item_attributes = {"brand": "ธนาคารทหารไทย", "brand_wikidata": "Q1527826"}

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
        (["แฟมิลี่มาร์ท", "FAMILYMART", "FAMILY MART"], FamilymartMYSpider.item_attributes),
        (["เซ็นทรัล", "CENTRAL"], {"brand": "Central Department Store", "brand_wikidata": "Q5060703"}),
        (["โรบินสัน", "ROBINSON"], {"brand": "Robinson Department Store", "brand_wikidata": "Q5060703"}),
        (["ฟู้ดแลนด์", "FOODLAND", "FOOD LAND"], {"brand": "Foodland", "brand_wikidata": "Q5465559"}),
        (["ซีพี", "CP"], CpFreshmartTHSpider.item_attributes),
        (["แมคโดนัลด์", "MCDONALDS", "MCDONALD"], McdonaldsSpider.item_attributes),
        (["CJ EXPRESS", "CJ. EXPRESS"], {"brand": "CJ Express", "brand_wikidata": "Q125874457"}),
        (["CJ MORE"], {"brand": "CJ More", "brand_wikidata": "Q125874457"}),
    ]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for key in ["location_branch", "location_atm"]:
            yield JsonRequest(
                url="https://www.ttbbank.com/api/location",
                data={"moduleKey": key},
                cb_kwargs={"key": key},
            )

    def parse(self, response, **kwargs):
        for location in response.json().get("body").get("data"):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
            item["phone"] = location.get("additional_phones")

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if times := location.get("{}_hours".format(day.lower())):
                    start_time, end_time = times.replace(".", ":").split("-")
                    item["opening_hours"].add_range(day, start_time.strip(), end_time.strip())

            if kwargs["key"] == "location_branch":
                item["ref"] = str(location.get("id")) + "- branch"
                apply_category(Categories.BANK, item)
            else:
                item["ref"] = str(location.get("id")) + "- atm"
                apply_category(Categories.ATM, item)
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    item.get("branch", ""), self.LOCATED_IN_MAPPINGS, self
                )

            yield item
