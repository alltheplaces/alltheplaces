from scrapy.http import JsonRequest
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, Fuel, FuelCards, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address

# We can get the first 250 from the API, but can't find a way to get the next 250 :(
# So instead get the ids from the sitemap and call the individual api endpoint
# "https://www.exxon.com/en/api/locator/Locations?DataSource=RetailGasStations",


# This data is also in Microsofts Virtual Earth, but we don't have a key with read access :(
# dataset_id = "5857976ca2ae4a8c9a546777ed33c1cd"
# dataset_name = "WEP2_Retail_PROD/RetailGasStations"


class ExxonMobilSpider(SitemapSpider):
    name = "exxonmobil"
    sitemap_urls = [
        "https://www.esso.co.uk/robots.txt",
        "https://www.esso.ca/robots.txt",
        "https://www.esso.no/robots.txt",
        "https://www.esso.lu/robots.txt",
        "https://www.esso.com.cy/robots.txt",
        "https://www.fuels.esso.co.th/robots.txt",
        "https://www.esso.com.sg/robots.txt",
        "https://www.mobil.co.nz/sitemap.xml",
        "https://www.esso.com.hk/robots.txt",
        "https://guam.mobil.com/robots.txt",
        "https://www.esso.de/robots.txt",
        "https://www.mobil.com.au/sitemap.xml",
        "https://carburanti.esso.it/robots.txt",
        "https://saipan.mobil.com/robots.txt",
        "https://www.exxon.com/robots.txt",
        "https://www.esso.be/robots.txt",
        "https://carburant.esso.fr/robots.txt",
        "https://www.esso.nl/robots.txt",
    ]
    sitemap_rules = [(r"/find-station/.+-\d+$", "parse")]
    download_delay = 0.5
    custom_settings = {"ROBOTSTXT_OBEY": False}

    brands = {
        "Exxon": {"brand": "Exxon", "brand_wikidata": "Q109675651"},
        "Mobil": {"brand": "Mobil", "brand_wikidata": "Q109676002"},
        "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
    }

    # Some countries/brands can be accessed by the US api, others need their own endpoint and some need a suffix
    api_override_map = {
        "www.esso.be": "https://www.esso.be/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}nl",
        "carburant.esso.fr": "https://carburant.esso.fr/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}fr",
        "www.esso.nl": "https://www.esso.nl/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}nl",
        "www.esso.no": "https://www.esso.no/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}nb",
        "www.esso.lu": "https://www.esso.lu/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}fr",
        "www.esso.com.cy": "https://www.esso.com.cy/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}el",
        "www.esso.com.sg": "https://www.esso.com.sg/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}",
        "www.mobil.co.nz": "https://www.mobil.co.nz/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}",
        "www.esso.com.hk": "https://www.esso.com.hk/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}zh",
        "guam.mobil.com": "https://guam.mobil.com/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}",
        "www.mobil.com.au": "https://www.mobil.com.au/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}",
        "www.esso.de": "https://www.esso.de/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}de",
        "carburanti.esso.it": "https://carburanti.esso.it/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}it",
    }

    # Rewrite the request to the API
    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            if request.callback == self.parse:
                domain = request.url.split("/")[2]
                ref = request.url.split("-")[-1]

                api_url = self.api_override_map.get(
                    domain,
                    "https://www.exxon.com/en/api/locator/Locations?DataSource=RetailGasStations&LocationID={ref}",
                ).format(ref=ref)
                request = JsonRequest(url=api_url, meta={"webpage": request.url})

            yield request

    def parse(self, response, **kwargs):
        for location in response.json()["Locations"]:
            if location["Brand"] == "Mobilcard":
                continue  # 170 NZ POIs that seem to third party ones that accept there loyalty cards

            item = DictParser.parse(location)
            item["ref"] = location["LocationID"]
            item["street_address"] = clean_address([location["AddressLine1"], location["AddressLine2"]])
            item["website"] = response.meta["webpage"]
            item["opening_hours"] = self.store_hours(location["HoursOfOperation24"])

            if brand := self.brands.get(location["Brand"]):
                item.update(brand)
            else:
                self.crawler.stats.inc_value(f"atp/exxonmobil/unknown_brand/{location['Brand']}")
                item["brand"] = location["Brand"]

            features = [f["Name"] for f in (location["FeaturedItems"] + location["StoreAmenities"])]

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.TOILETS, item, "Restroom" in features, True)
            apply_yes_no(Extras.TOILETS, item, "Customer Toilets" in features, True)
            apply_yes_no(Extras.TOILETS, item, "Toilets" in features, True)
            apply_yes_no(Extras.ATM, item, "ATM" in features, True)
            apply_yes_no(Extras.ATM, item, "ATM  DBS" in features, True)
            apply_yes_no(Extras.CAR_WASH, item, "Carwash" in features, True)
            apply_yes_no(Extras.CAR_WASH, item, "Jet Wash" in features, True)
            apply_yes_no(Extras.CAR_WASH, item, "Touchless Carwash" in features, True)
            apply_yes_no(Extras.COMPRESSED_AIR, item, "Air Tower  Air" in features)
            apply_yes_no(Extras.WHEELCHAIR, item, "Disability Fueling Assistance" in features)

            apply_yes_no(PaymentMethods.APPLE_PAY, item, "Apple Pay" in features)
            apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "Google Pay" in features)

            apply_yes_no("self_service", item, "Pay at the Pump" in features, True)
            apply_yes_no("self_service", item, "Self Service" in features, True)
            apply_yes_no("self_service", item, "24 Hour Pay at the Pump" in features, True)
            apply_yes_no("self_service", item, "Pay at Pump" in features, True)
            apply_yes_no("full_service", item, "Full Service" in features)
            apply_yes_no("capacity:hgv", item, "HGV Truck Pumps" in features)

            # Other popular ones include:
            # "Synergy Supremeplus Premium Gasoline"
            # "Exxon Mobil Rewardsplus"
            # "Synergy Extra Gasoline"
            # "Synergy Diesel Efficient  Diesel"
            # "Vacuum"
            # "Synergy Diesel"
            # "Synergy Diesel Efficient"
            # "Synergy Image"
            # "Synergy Unleaded 95"
            # "Synergy Supremeplus Diesel"
            # "Speedpassplus"
            # "AdBlue Cans"
            # "PC Optimum"
            # "Auto Repair"
            # "Servitissimo"
            # "Synergy Supremeplus Unleaded 98"
            # "Esso Extras"
            # "Esso App Mobile Payment"
            # "Esso Voucher Acceptance"
            # "Just for UParticipating"
            # "Gasohol 95"
            # "Supremeplus Diesel"
            # "Synergy Super 95"
            # "Other Service Bay Brand"
            # "Synergy Super E10 95"
            # "Commercial Truck Fueling"
            # "AdBlue Bulk"
            # "High Flow Diesel"
            # "Supremeplus Gasohol 95"
            # "ACME Gas Rewards Participating"
            # "Synergy Supremeplus 98"
            # "Safeway Gas Rewards Participating"
            # "Synergy Special Diesel"
            # "Mobil Smiles Acceptor"
            # "Synergy Extra Diesel"
            # "Synergy Extra Unleaded 91"
            # "Shaws Gas Rewards Participating"
            # "Synergy Euro Unleaded 95"
            # "Unleaded 95"
            # "Synergy Unleaded 95 E10"
            # "LPG Swap a Bottle"
            # "Synergy Extra 95"
            # "Synergy Super SP95"
            # "Synergy Special ULP"
            # "Synergy Supreme 952"
            # "Synergy Agricultural Diesel"
            # "Synergy Special E10"
            # "Energy Supreme Diesel"
            # "Premium Unleaded 95"

            # "Commercial Diesel Fleet Cards Accepted"
            apply_yes_no(FuelCards.ESSO_NATIONAL, item, "Esso Card" in features)
            apply_yes_no(FuelCards.DKV, item, "DKV Card" in features)
            apply_yes_no(FuelCards.UTA, item, "UTA Card" in features)
            # "Payback Card"
            apply_yes_no(FuelCards.SHELL, item, "Shell Card" in features)
            apply_yes_no(FuelCards.EXXONMOBIL_FLEET, item, "ExxonMobil Fleet Card" in features)
            apply_yes_no(FuelCards.DEUTSCHLAND, item, "DeutschlandCard" in features)
            apply_yes_no(FuelCards.BP, item, "BP card" in features)
            apply_yes_no(FuelCards.ALLSTAR, item, "Allstar Card" in features)
            apply_yes_no(FuelCards.LOGPAY, item, "LogPay Card" in features)
            # "Travel Card"
            apply_yes_no(FuelCards.AVIA, item, "Avia Card" in features)
            apply_yes_no(FuelCards.MOBIL, item, "Mobilcard" in features, True)
            apply_yes_no(FuelCards.MOBIL, item, "Mobilcard Acceptor Site" in features, True)
            apply_yes_no(FuelCards.MOBIL, item, "Mobilcard Discount Site" in features, True)
            apply_yes_no(FuelCards.MOBIL, item, "Mobil Card" in features, True)
            # "Albertsons Gas Rewards Participating"

            apply_yes_no(Fuel.DIESEL, item, "Diesel" in features)
            apply_yes_no(Fuel.E10, item, "Synergy Regular Gasoline" in features)
            apply_yes_no(Fuel.PROPANE, item, "Propane" in features)
            apply_yes_no(Fuel.LPG, item, "LPG" in features)
            apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in features)
            apply_yes_no(Fuel.ELECTRIC, item, "Electric Charger" in features, True)
            apply_yes_no(Fuel.ELECTRIC, item, "Electric Vehicle Charging" in features, True)

            # if "Convenience Store" in features:
            #    apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item

    @staticmethod
    def store_hours(hours: str) -> OpeningHours:
        """
        :param hours: hours to convert come in format "04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;"
        :return: OpeningHours
        """
        oh = OpeningHours()
        for index, times in enumerate(hours.strip(";").split(";")):
            if not times or times == "Closed":
                continue
            if times == "All Day":
                times = "00:00,23:59"
            try:
                start_time, end_time = times.split(",")
                oh.add_range(DAYS[index], start_time, end_time)
            except:  # A few edge cases like "2200" not "22:00"
                pass

        return oh
