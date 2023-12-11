import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

BASH_BRANDS = {
    "ASJ": {"brand": "American Swiss", "brand_wikidata": "Q116430764"},
    "AMERICAN SWISS": {"brand": "American Swiss", "brand_wikidata": "Q116430764"},
    "ARCHIVE": {"brand": "Archive", "brand_wikidata": "Q116431114"},
    "CHARLES & KEITH": {
        "brand": "Charles & Keith",
        "brand_wikidata": "Q3878818",
        "extras": Categories.SHOP_CLOTHES.value,
    },
    "COLETTE": {"brand": "Colette", "brand_wikidata": "Q737606", "extras": Categories.SHOP_CLOTHES.value},
    "EXACT": {"brand": "Exact", "brand_wikidata": "Q116379381"},
    "EX": {"brand": "Exact", "brand_wikidata": "Q116379381"},
    "DONNA": {"brand": "Donna", "brand_wikidata": "Q117407190", "extras": Categories.SHOP_VARIETY_STORE.value},
    "DS": {"brand": "Duesouth", "brand_wikidata": "Q117406776", "extras": Categories.SHOP_VARIETY_STORE.value},
    "DUESOUTH": {"brand": "Duesouth", "brand_wikidata": "Q117406776", "extras": Categories.SHOP_VARIETY_STORE.value},
    "FABIANI": {"brand": "Fabiani", "brand_wikidata": "Q116379050"},
    "FB": {"brand": "Fabiani", "brand_wikidata": "Q116379050"},
    "FIX": {"brand": "The FIX", "brand_wikidata": "Q116379523"},
    "FOSCHINI": {"brand": "Foschini", "brand_wikidata": "Q116391780"},
    "FOS": {"brand": "Foschini", "brand_wikidata": "Q116391780"},
    "G-STAR RAW": {"brand": "G-Star RAW", "brand_wikidata": "Q1484081"},
    "G-STAR": {"brand": "G-Star RAW", "brand_wikidata": "Q1484081"},
    "HI": {"brand": "hi", "brand_wikidata": "Q116431177", "extras": Categories.SHOP_CLOTHES.value},
    "@HOME LIVINGSPACE": {"brand": "@Home Livingspace", "brand_wikidata": "Q117406343"},
    "@HOME": {"brand": "@Home", "brand_wikidata": "Q116429887"},
    "LUELLA": {"brand": "Luella", "brand_wikidata": "Q117406783", "extras": Categories.SHOP_VARIETY_STORE.value},
    "JET": {"brand": "Jet", "brand_wikidata": "Q61995123"},
    "MARKHAM": {"brand": "Markham", "brand_wikidata": "Q116378583"},
    "MAT & MAY": {
        "brand": "Mat & May",
        "brand_wikidata": "Q117406655",
        "extras": Categories.SHOP_FASHION_ACCESSORIES.value,
    },
    "MATRIX": {
        "brand": "Matrix Warehouse Computers",
        "brand_wikidata": "Q117407296",
        "extras": Categories.SHOP_COMPUTER.value,
    },
    "MK": {"brand": "Markham", "brand_wikidata": "Q116378583"},
    "NEXT": {"brand": "Next", "brand_wikidata": "Q246655"},
    "RELAY JEANS": {"brand": "Relay Jeans", "brand_wikidata": "Q116378360"},
    "RFO": {"brand": "Renegade Fashion Outlet", "brand_wikidata": "Q116457467"},
    "SB": {"brand": "SODA Bloc", "brand_wikidata": "Q117406709", "extras": Categories.SHOP_CLOTHES.value},
    "SF": {"brand": "The Sneaker Factory", "brand_wikidata": "Q116290301"},
    "SNEAKER FACTORY": {"brand": "The Sneaker Factory", "brand_wikidata": "Q116290301"},
    "SODA BLOC": {"brand": "SODA Bloc", "brand_wikidata": "Q117406709", "extras": Categories.SHOP_CLOTHES.value},
    "SPORTSCENE": {"brand": "Sportscene", "brand_wikidata": "Q116378841"},
    "SS": {"brand": "Sportscene", "brand_wikidata": "Q116378841"},
    "STERNS": {"brand": "Sterns", "brand_wikidata": "Q116430300"},
    "STN": {"brand": "Sterns", "brand_wikidata": "Q116430300"},
    "TOTALSPORTS": {"brand": "Totalsports", "brand_wikidata": "Q116379123"},
    "TS": {"brand": "Totalsports", "brand_wikidata": "Q116379123"},
    "THE FIX": {"brand": "The FIX", "brand_wikidata": "Q116379523"},
    "THE SCENE": {"brand": "The Scene", "brand_wikidata": "Q117406601", "extras": Categories.SHOP_CLOTHES.value},
}


class BashZASpider(Spider):
    name = "bash_za"
    allowed_domains = ["bash.com"]
    start_urls = [
        'https://bash.com/_v/public/graphql/v1?operationName=getStores&extensions={"persistedQuery":{"version":1,"sha256Hash":"53e625f7c1d5013253fe27c99d9d0b4f9aba2545fffe7b5d8691efbe57ff419c","sender":"thefoschini.store-locator@0.x","provider":"thefoschini.store-locator@0.x"}}'
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]["getStores"]["items"]:
            location["name"] = location["name"].strip()
            if not location["isActive"] or location["name"] in [
                "TFG Money Account Payment",
                "MARKRAND",
                "T B A",
                "DIEPSLOOT",
                "ELIM MALL",
            ]:
                continue
            item = DictParser.parse(location)
            item["name"] = item.pop("name").replace("Sportcene", "Sportscene")
            item["lat"] = location["address"]["location"]["latitude"]
            item["lon"] = location["address"]["location"]["longitude"]
            item.pop("street")
            item["street_address"] = " ".join(
                filter(None, [location["address"]["street"], location["address"]["complement"]])
            ).strip()
            item["website"] = (
                "https://bash.com/store/"
                + item["name"].lower().replace(" ", "-")
                + "-"
                + item["postcode"]
                + "/"
                + item["ref"]
            )
            item["opening_hours"] = OpeningHours()
            for hours_range in location["businessHours"]:
                item["opening_hours"].add_range(
                    DAYS[hours_range["dayOfWeek"]], hours_range["openingTime"], hours_range["closingTime"], "%H:%M:%S"
                )

            brands_regex_group = r"|".join(BASH_BRANDS)
            brand_name_regex = r"^(" + brands_regex_group + r") "
            if m := re.match(brand_name_regex, item["name"], flags=re.IGNORECASE):
                item.update(BASH_BRANDS[m.group(1).upper()])

            yield item
