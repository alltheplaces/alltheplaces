import json

from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT

GAMESTOP_SHARED_ATTRIBUTES = {
    "brand": "GameStop",
    "brand_wikidata": "Q202210",
    "extras": Categories.SHOP_VIDEO_GAMES.value,
}


class GamestopUSSpider(Spider):
    name = "gamestop_us"
    item_attributes = GAMESTOP_SHARED_ATTRIBUTES
    allowed_domains = ["www.gamestop.com"]
    start_urls = [
        "https://www.gamestop.com/on/demandware.store/Sites-gamestop-us-Site/default/Stores-FindStores?hasCondition=false&hasVariantsAvailableForLookup=false&hasVariantsAvailableForPickup=false&source=plp&showMap=false&products=undefined:1"
    ]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_delay = 0.2

    def start_requests(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://www.gamestop.com/stores/",
            "X-Requested-With": "XMLHttpRequest",
        }
        for url in self.start_urls:
            # There appears to be no way via the website or API to
            # list all stores or perform a coordinate/radius or
            # bounding box search. A postcode search appears to be
            # the only option and there are almost 38000 postcodes
            # in the US (38000 API requests to Gamestop). It is
            # possible to reduce the list of postcodes to search
            # by ignoring postcodes with low populations. There are
            # fancier and more accurate ways to reduce the list of
            # postcodes to those which are useful, but this is not
            # yet implemented in ATP and is a complex problem
            # requiring significant experimentation and
            # documentation to explain the methodology which others
            # can reproduce.
            #
            # The 2022 Annual Report (https://news.gamestop.com/static-files/fe325562-c087-4fad-809c-efd183364196)
            # states that there were 2949 open stores at 28 Jan 2023
            # operating in the US.
            #
            # One year later, the following search results were
            # observed for different population filter values:
            # 1. Population > 30000: 2843 locations returned
            #    from 2013 requests to the API.
            # 2. Population > 50000: 2824 locations returned
            #    from 629 requests to the API.
            #
            # This spider picks option (2) as a balance between
            # minimising API requests and obtaining as many
            # locations as possible.
            #
            # A website tracking Gamestop store closures indicates
            # that 55 stores were known to have closed in 2023 and
            # to the end of January 2024. Reference:
            # https://gsclosing.blogspot.com/
            #
            # The error margin therefore appears to be ~70 stores
            # (<2.5%) which this spider may miss due to reduction
            # in postcodes which are searched for stores.
            #
            # Note the search radius can be increased above 200
            # however this will result in API failures because
            # there is a limit of a 3MB response and 1 million
            # characters returned.
            for postal_region in postal_regions("US", min_population=50000, consolidate_cities=True):
                postcode = postal_region["postal_region"]
                yield FormRequest(
                    url=url,
                    method="POST",
                    headers=headers,
                    formdata={"postalCode": str(postcode), "radius": "200", "csrf_token": "0"},
                )

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["name"] = item["name"].replace(" - GameStop", "")
            if location.get("address2"):
                suite = location.get("address2").upper().replace("STE", "Suite")
                item["street_address"] = clean_address([suite, location.get("address1")])
            item["website"] = "https://www.gamestop.com/search/?store=" + item["ref"]
            item["opening_hours"] = OpeningHours()
            for day_hours in json.loads(location.get("storeOperationHours")):
                item["opening_hours"].add_range(day_hours["day"], day_hours["open"], day_hours["close"], "%H%M")
            yield item
