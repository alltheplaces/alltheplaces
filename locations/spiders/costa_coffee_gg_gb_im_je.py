from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class CostaCoffeeGGGBIMJESpider(Spider):
    name = "costa_coffee_gg_gb_im_je"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["www.costa.co.uk"]
    start_urls = ["https://www.costa.co.uk/api/mdm/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # No robots.txt. 404 HTML page returned instead.

    def start_requests(self):
        graphql_query_template = """query Sites {
    sites(
        siteStatuses: ["OPEN"]
        tradingStatusAvailable: true
        geo: {
            latitude: __LATITUDE__
            longitude: __LONGITUDE__
        }
        countries: "GB"
        orderBy: { distance: ASC }
        first: 2500
    ) {
        items {
            id
            extendedName: name
            location {
                address {
                    address1
                    address2
                    city
                    postCode
                }
                geo {
                    latitude
                    longitude
                    distanceMiles
                }
            }
            siteType
            facilities {
                babyChanging
                clickAndServe
                coffeeClub
                collect
                delivery
                disabledAccess
                disabledWC
                driveThru
                giftCard
                preOrderCollect
                tooGoodToGo
                wifi
            }
            expressMachines {
                characteristics {
                    icedDrinks
                }
            }
            operatingHours(timeTypes: ["Standard"]) {
                Monday: monday {
                    open24Hours
                    open
                    close
                }
                Tuesday: tuesday {
                    open24Hours
                    open
                    close
                }
                Wednesday: wednesday {
                    open24Hours
                    open
                    close
                }
                Thursday: thursday {
                    open24Hours
                    open
                    close
                }
                Friday: friday {
                    open24Hours
                    open
                    close
                }
                Saturday: saturday {
                    open24Hours
                    open
                    close
                }
                Sunday: sunday {
                    open24Hours
                    open
                    close
                }
            }
            name: knownAs
        }
    }
}"""
        for lat, lon in country_iseadgg_centroids(["GG", "GB", "IM", "JE"], 48):
            graphql_query = graphql_query_template.replace("__LATITUDE__", str(lat)).replace("__LONGITUDE__", str(lon))
            yield JsonRequest(url=self.start_urls[0], data={"query": graphql_query})

    def parse(self, response):
        locations = response.json()["data"]["sites"]["items"]

        if len(locations) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))

        for location in locations:
            item = DictParser.parse(location)

            if location["siteType"] == "Global Express":
                item["brand"] = "Costa Express"
                item["brand_wikidata"] = "Q113556385"
                apply_category(Categories.VENDING_MACHINE_COFFEE, item)
            else:
                apply_category(Categories.COFFEE_SHOP, item)

            item["lat"] = location["location"]["geo"]["latitude"]
            item["lon"] = location["location"]["geo"]["longitude"]
            item["street_address"] = clean_address(
                [location["location"]["address"]["address1"], location["location"]["address"]["address2"]]
            )
            item["city"] = location["location"]["address"]["city"]

            item["postcode"] = location["location"]["address"]["postCode"]
            if item["postcode"]:
                if item["postcode"][:2] == "GY":
                    item["country"] = "GG"
                elif item["postcode"][:2] == "IM":
                    item["country"] = "IM"
                elif item["postcode"][:2] == "JE":
                    item["country"] = "JE"
                else:
                    item["country"] = "GB"

            if len(location["operatingHours"]) > 0:
                item["opening_hours"] = OpeningHours()
                for day_name, day_hours in location["operatingHours"][0].items():
                    if day_hours["open24Hours"]:
                        item["opening_hours"].add_range(day_name, "00:00", "24:00")
                    else:
                        item["opening_hours"].add_range(day_name, day_hours["open"], day_hours["close"])

            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, location["facilities"].get("babyChanging"), False)
            apply_yes_no(Extras.DELIVERY, item, location["facilities"].get("delivery"), False)
            apply_yes_no(Extras.WHEELCHAIR, item, location["facilities"].get("disabledAccess"), False)
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, location["facilities"].get("disabledWC"), False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["facilities"].get("driveThru"), False)
            apply_yes_no(Extras.WIFI, item, location["facilities"].get("wifi"), False)

            yield item
