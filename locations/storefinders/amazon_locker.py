from typing import AsyncIterator, Iterable

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Request, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.country_utils import CountryUtils
from locations.geo import city_locations, postal_regions
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

# located_in for storeType in API response
STORE_TYPES = {
    "AMAZON_WFM": {"located_in": "Whole Foods Market", "located_in_wikidata": "Q1809448"},
    "AMAZON_GO": {"located_in": "Amazon Go", "located_in_wikidata": "Q27676067"},
    "AMAZON_FRESH": {"located_in": "Amazon Fresh", "located_in_wikidata": "Q4740834"},
}
# located_in for business names in the address line
# TODO: Don't require an exact match and include the proper name in the list
BRANDS_IN_ADDRESS = {
    "76": "Q1658320",
    "7-Eleven": "Q259340",
    "Ace Hardware": "Q4672981",
    "Albertsons": "Q2831861",
    "Arco": "Q304769",
    "Boost Mobile": "Q4943790",
    "BP": "Q152057",
    "Burlington": "Q4999220",
    "Cardenas": "Q64149543",
    "Carl's Jr.": "Q1043486",
    "CEFCO": "Q110209230",
    "Chase": "Q524629",
    "Chevron": "Q319642",
    "Church's Chicken": "Q1089932",
    "Circle K": "Q3268010",
    "Citgo": "Q2974437",
    "Conoco": "Q109341187",
    "D'Agostino": "Q20656844",
    "dd's Discounts": "Q83743863",
    "Dollar Tree": "Q5289230",
    "Domino's": "Q839466",
    "DoubleTree": "Q2504643",
    "Embassy Suites": "Q5369524",
    "Exxon": "Q109675651",
    "Family Dollar": "Q5433101",
    "Family Fare": "Q19868045",
    "FAST STOP": "Q116734101",
    "Five Below": "Q5455836",
    "FoodMaxx": "Q61894844",
    "GetGo": "Q5553766",
    "Giant Eagle": "Q1522721",
    "Godfather's Pizza": "Q5576353",
    "Gold's Gym": "Q1536234",
    "Goodwill": "Q5583655",
    "Hilton": "Q598884",
    "Hilton Garden Inn": "Q1162859",
    "Holiday": "Q5880490",
    "Home2 Suites": "Q5887912",
    "Homewood Suites": "Q5890701",
    "LA Fitness": "Q6457180",
    "Love's": "Q1872496",
    "Lucky": "Q6698032",
    "Market District": "Q98550869",
    "McDonald's": "Q38076",
    "Metro by T-Mobile": "Q1925685",
    "Minit Mart": "Q18154470",
    "Mirabito": "Q126489051",
    "Mobil": "Q109676002",
    "Payomatic": "Q48742899",
    "Petro": "Q64051305",
    "Phillips 66": "Q1656230",
    "Piggly Wiggly": "Q3388303",
    "QuickChek": "Q7271689",
    "Rent-A-Center": "Q7313497",
    "Ridley's Family Markets": "Q7332999",
    "Rite Aid": "Q3433273",
    "Road Ranger": "Q7339377",
    "Rocket": "Q121513516",
    "Rosauers": "Q7367458",
    "Safeway": "Q17111901",
    "Save-A-Lot": "Q7427972",
    "Save Mart": "Q7428009",
    "Shell": "Q110716465",
    "Shoppers": "Q7501183",
    "Speedway": "Q7575683",
    "Sunoco": "Q1423218",
    "TA": "Q7835892",
    "TA Express": "Q7835892",
    "Terrible's": "Q7703648",
    "Texaco": "Q775060",
    "True Value": "Q7847545",
    "Valero": "Q1283291",
    "Vons": "Q7941609",
    "Whole Foods Market": "Q1809448",
}


class AmazonLockerSpider(JSONBlobSpider):
    allowed_domains: list[str] = []
    item_attributes: dict = {
        "brand": "Amazon Locker",
        "brand_wikidata": "Q16974764",
    }
    locations_key: str | list[str] = "locationList"

    async def start(self) -> AsyncIterator[Request]:
        country_utils = CountryUtils()
        if len(self.allowed_domains) != 1:
            raise ValueError("Specify one domain name in the allowed_domains list attribute.")
            return
        for country in country_utils.country_codes_from_spider_name(self.name):
            if country in ("GB", "US", "FR"):
                # Tested in US to be the maximum population limit that still returns all lockers
                regions = postal_regions(country, 6799)
            else:
                regions = city_locations(country, 6799)
            for region in regions:
                yield Request(
                    f"https://{self.allowed_domains[0]}/location_selector/fetch_locations?longitude={region['longitude']}&latitude={region['latitude']}&clientId=amazon_us_add_to_addressbook_mkt_mobile&countryCode={country}&sortType=DISTANCE"
                )

    def parse(self, response: TextResponse) -> Iterable[Feature | Request]:
        if response.json().get("isErrored", True) and response.request:
            # Usually intermittent
            if retry_request := get_retry_request(response.request, spider=self):
                yield retry_request
        else:
            yield from super().parse(response)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # Only process actual lockers.
        if feature["accessPointType"] != "LOCKER":
            return

        if feature["addressLine1"] in BRANDS_IN_ADDRESS:
            # addressLine1 is frequently the name of the business it's in.
            # But not always, so only remove it if it's a known brand.
            located_in = feature.pop("addressLine1")
            item["located_in"] = located_in
            item["located_in_wikidata"] = BRANDS_IN_ADDRESS[located_in]
        if feature["storeType"]:
            item.update(STORE_TYPES[feature["storeType"]])

        item["street_address"] = merge_address_lines(
            [feature.get("addressLine1"), feature.get("addressLine2"), feature.get("addressLine3")]
        )
        item["state"] = feature["stateOrRegion"]

        if feature["isRestricted"]:
            item["extras"]["access"] = "private"

        apply_yes_no(Extras.WHEELCHAIR, item, feature["hasLowerLocker"])

        item["opening_hours"] = OpeningHours()
        for hours in feature["operationalInfo"]:
            item["opening_hours"].add_ranges_from_string(f"{hours['operationalDayOfWeek']} {hours['operationalHours']}")

        apply_category(Categories.PARCEL_LOCKER, item)

        yield item


# Country codes from spider name are used for both the coordinate list and the API parameter.
# The list of domains is from https://www.amazon.com/customer-preferences/country
# The list of country codes for each domain is from that domain's locker search page at <domain>/ulp
# Each domain has been split into a separate spider for better parallelism during the weekly run.

# Domains removed for having no lockers:

# class AmazonLockerAESpider(AmazonLockerSpider):
#    name = "amazon_locker_ae"
#    allowed_domains = ["www.amazon.ae"]

# class AmazonLockerBESpider(AmazonLockerSpider):
#    name = "amazon_locker_be"
#    allowed_domains = ["www.amazon.com.be"]

# class AmazonLockerBRSpider(AmazonLockerSpider):
#    name = "amazon_locker_br"
#    allowed_domains = ["www.amazon.com.br"]

# class AmazonLockerEGSpider(AmazonLockerSpider):
#    name = "amazon_locker_eg"
#    allowed_domains = ["www.amazon.eg"]

# TODO: The API exists and returns a response, but the response is always an error.
# class AmazonLockerIESpider(AmazonLockerSpider):
#    name = "amazon_locker_ie"
#    allowed_domains = ["www.amazon.ie"]
#    requires_proxy = "ie"

# class AmazonLockerINSpider(AmazonLockerSpider):
#    name = "amazon_locker_in"
#    allowed_domains = ["www.amazon.in"]

# class AmazonLockerPLSpider(AmazonLockerSpider):
#    name = "amazon_locker_pl"
#    allowed_domains = ["www.amazon.pl"]

# class AmazonLockerSASpider(AmazonLockerSpider):
#    name = "amazon_locker_sa"
#    allowed_domains = ["www.amazon.sa"]

# class AmazonLockerSESpider(AmazonLockerSpider):
#    name = "amazon_locker_se"
#    allowed_domains = ["www.amazon.se"]

# class AmazonLockerSGSpider(AmazonLockerSpider):
#    name = "amazon_locker_sg"
#    allowed_domains = ["www.amazon.sg"]

# class AmazonLockerTRSpider(AmazonLockerSpider):
#    name = "amazon_locker_tr"
#    allowed_domains = ["www.amazon.com.tr"]

# class AmazonLockerZASpider(AmazonLockerSpider):
#    name = "amazon_locker_za"
#    allowed_domains = ["www.amazon.co.za"]
