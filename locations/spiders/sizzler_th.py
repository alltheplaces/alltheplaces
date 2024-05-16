import scrapy
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class SizzlerTHSpider(scrapy.Spider):
    name = "sizzler_th"
    item_attributes = {
        "brand": "Sizzler",
        "brand_wikidata": "Q1848822",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    thailand_provinces = [
        "Bangkok",
        "Amnat Charoen",
        "Ang Thong",
        "Bueng Kan",
        "Buriram",
        "Chachoengsao",
        "Chai Nat",
        "Chaiyaphum",
        "Chanthaburi",
        "Chiang Mai",
        "Chiang Rai",
        "Chonburi",
        "Chumphon",
        "Kalasin",
        "Kamphaeng Phet",
        "Kanchanaburi",
        "Khon Kaen",
        "Krabi",
        "Lampang",
        "Lamphun",
        "Loei",
        "Lopburi",
        "Mae Hong Son",
        "Maha Sarakham",
        "Mukdahan",
        "Nakhon Nayok",
        "Nakhon Pathom",
        "Nakhon Phanom",
        "Nakhon Ratchasima",
        "Nakhon Sawan",
        "Nakhon Si Thammarat",
        "Nan",
        "Narathiwat",
        "Nong Bua Lamphu",
        "Nong Khai",
        "Nonthaburi",
        "Pathum Thani",
        "Pattani",
        "Phang Nga",
        "Phatthalung",
        "Phayao",
        "Phetchabun",
        "Phetchaburi",
        "Phichit",
        "Phitsanulok",
        "Phra Nakhon Si Ayutthaya",
        "Phrae",
        "Phuket",
        "Prachin Buri",
        "Prachuap Khiri Khan",
        "Ranong",
        "Ratchaburi",
        "Rayong",
        "Roi Et",
        "Sa Kaeo",
        "Sakon Nakhon",
        "Samut Prakan",
        "Samut Sakhon",
        "Samut Songkhram",
        "Saraburi",
        "Satun",
        "Sing Buri",
        "Sisaket",
        "Songkhla",
        "Sukhothai",
        "Suphan Buri",
        "Surat Thani",
        "Surin",
        "Tak",
        "Trang",
        "Trat",
        "Ubon Ratchathani",
        "Udon Thani",
        "Uthai Thani",
        "Uttaradit",
        "Yala",
        "Yasothon",
    ]

    def start_requests(self):
        for province in self.thailand_provinces:
            yield Request(
                url=f"https://www.sizzler.co.th/api/search/location?location=&province={province}&lang=en",
                cb_kwargs={"province": province},
            )

    def parse(self, response, province):
        locations = response.json()
        if len(locations) > 0:
            for location in locations:
                item = DictParser.parse(location)
                item["state"] = province
                item["addr_full"] = location.get("address_th")
                item["extras"]["addr:full:en"] = location.get("address_en")
                item["extras"]["check_date"] = location.get("updated_at")

                yield item
