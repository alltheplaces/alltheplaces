import re

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request

from locations.categories import Categories
from locations.hours import DAYS, OpeningHours
from locations.items import get_lat_lon, set_closed
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address

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
    "CORICRAFT": {"brand": "Coricraft", "brand_wikidata": "Q116428628"},
    "DIAL A BED": {"brand": "Dial-a-Bed", "brand_wikidata": "Q116429178"},
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
    "THE BED STORE": {"brand": "The Bed Store", "brand_wikidata": "Q116429563"},
    "THE SCENE": {"brand": "The Scene", "brand_wikidata": "Q117406601", "extras": Categories.SHOP_CLOTHES.value},
    "VOLPES": {"brand": "Volpes", "brand_wikidata": "Q116431266"},
}


class BashSpider(JSONBlobSpider):
    name = "bash"
    allowed_domains = ["bash.com"]
    start_urls = ["https://bash.com/store-finder"]

    def start_requests(self):
        self.brand_name_regex = re.compile(r"^(" + "|".join(BASH_BRANDS) + r") ", re.IGNORECASE)
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_json)

    def fetch_json(self, response):
        cache_hints = parse_js_object(
            response.xpath('.//script[contains(text(), "thefoschini.store-locator@0.x")]/text()').get()
        )["cacheHints"]
        url_hash = [h for h in cache_hints if cache_hints[h].get("provider") == "thefoschini.store-locator@0.x"][0]
        yield JsonRequest(
            url='https://bash.com/_v/public/graphql/v1?operationName=getStores&extensions={"persistedQuery":{"version":1,"sha256Hash":"'
            + url_hash
            + '","sender":"thefoschini.store-locator@0.x","provider":"thefoschini.store-locator@0.x"}}',
            callback=self.parse,
        )

    def extract_json(self, response):
        return response.json()["data"]["getStores"]["items"]

    def post_process_item(self, item, response, location):
        location["name"] = location["name"].strip()
        if not location["isActive"] or location["name"] in [
            "TFG Money Account Payment",
            "MARKRAND",
            "T B A",
            "DIEPSLOOT",
            "ELIM MALL",
        ]:
            return
        if " (CLOSED) " in item["name"]:
            set_closed(item)

        item["lat"] = location["address"]["location"]["latitude"]
        item["lon"] = location["address"]["location"]["longitude"]
        item.pop("street")
        item["street_address"] = clean_address([location["address"]["street"], location["address"]["complement"]])
        item["state"], item["country"] = self.clean_state(item["state"])

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

        if m := self.brand_name_regex.match(item["name"]):
            item.update(BASH_BRANDS[m.group(1).upper()])
            item["branch"] = (
                item["name"]
                .replace(self.brand_name_regex.match(item["name"]).group(1), "")
                .replace("Sportcene", "")
                .strip()
            )
        # If it's at null island it will get dropped anyway
        # There are a number of non-real locations with 0,0 coordinates
        elif get_lat_lon(item) != (float(0), float(0)):
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{item['name']}")
            item["branch"] = item["name"]
        item.pop("name")

        yield item

    def clean_state(self, state: str) -> tuple:
        actually_countries = {
            "BOTSWANA": "BW",
            "NAMIBIA": "NA",
            "SWAZILAND": "SZ",
        }
        ZA_PROVINCES = [
            "Eastern Cape",
            "Free State",
            "Gauteng",
            "KwaZulu-Natal",
            "Limpopo",
            "Mpumalanga",
            "North West",
            "Northern Cape",
            "Western Cape",
        ]
        other_states = {
            "Butha-Buthe": ("Butha-Buthe", "LS"),
            "Leribe": ("Leribe", "LS"),
            "Lusaka": (None, "ZM"),
            "Maseru": ("Maseru", "LS"),
            "Mohale's Hoek": ("Mohale's Hoek", "LS"),
            "NAIROBI": (None, "KE"),
        }
        if state in actually_countries:
            return (None, actually_countries[state])
        if state in other_states:
            return other_states[state]
        for province in ZA_PROVINCES:
            if state.lower().replace("-", " ") == province.lower().replace("-", " "):
                return (province, "ZA")

        self.crawler.stats.inc_value(f"atp/{self.name}/unknown_state/{state}")
        return (state, None)
