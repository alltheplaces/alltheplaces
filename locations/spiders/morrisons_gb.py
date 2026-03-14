import re

from scrapy import Request, Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.central_england_cooperative import set_operator


class MorrisonsGBSpider(Spider):
    name = "morrisons_gb"
    allowed_domains = ["api.morrisons.com", "my.morrisons.com"]
    start_urls = ["https://api.morrisons.com/location/v2/stores?apikey=kxBdM2chFwZjNvG2PwnSn3sj6C53dLEY&limit=20000"]

    MCCOLLS = {"brand": "McColl's", "brand_wikidata": "Q16997477"}
    MARTINS = {"brand": "Martin's", "brand_wikidata": "Q116779207"}
    RS_MCCOLL = {"brand": "RS McColl", "brand_wikidata": "Q7277785"}
    MORRISONS = {"brand": "Morrisons", "brand_wikidata": "Q922344"}
    MORRISONS_DAILY = {"brand": "Morrisons Daily", "brand_wikidata": "Q99752411"}
    MORRISONS_SELECT = {"brand": "Morrisons Select", "brand_wikidata": "Q105221633"}

    def create_slug(self, name: str) -> str:
        a = "àáäâãåăæąçćčđďèéěėëêęğǵḧìíïîįłḿǹńňñòóöôœøṕŕřßşśšșťțùúüûǘůűūųẃẍÿýźžż·/_,:;"
        b = "aaaaaaaaacccddeeeeeeegghiiiiilmnnnnooooooprrsssssttuuuuuuuuuwxyyzzz------"

        slug = re.sub(r"\s+", "-", name.lower())

        for old, new in zip(a, b):
            slug = slug.replace(old, new)

        slug = slug.replace("&", "-and-")
        slug = re.sub(r"[^\w\-]+", "", slug)
        slug = re.sub(r"\-\-+", "-", slug)
        slug = slug.strip("-")

        return slug

    def parse(self, response):
        for location in response.json()["stores"]:
            location["id"] = str(location.pop("name"))
            item = DictParser.parse(location)
            item["street_address"] = clean_address(
                [location["address"].get("addressLine1"), location["address"].get("addressLine2")]
            )
            item["website"] = "https://my.morrisons.com/storefinder/{}/{}".format(
                item["ref"], self.create_slug(location["storeName"])
            )

            item["opening_hours"] = OpeningHours()
            for day_abbrev, day_hours in location["openingTimes"].items():
                item["opening_hours"].add_range(day_abbrev, day_hours["open"], day_hours["close"], "%H:%M:%S")

            if location["storeFormat"] == "supermarket" and location["category"] == "Supermarket":
                item.update(self.MORRISONS)
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif location["storeFormat"] == "supermarket" and (
                location["category"] == "McColls" or location["category"] == "Franchise"
            ):
                if "Morrisons Daily" in location["storeName"]:
                    item.update(self.MORRISONS_DAILY)
                elif "McColl's" in location["storeName"]:
                    item.update(self.MCCOLLS)
                elif "Rs Mccoll" in location["storeName"]:
                    item.update(self.RS_MCCOLL)
                elif "Martin's" in location["storeName"]:
                    item.update(self.MARTINS)
                apply_category(Categories.SHOP_CONVENIENCE, item)
                set_operator(self.MCCOLLS, item)
            elif location["storeFormat"] == "supermarket" and location["category"] == "Gas Station":
                if "Morrisons Daily" in location["storeName"]:
                    item.update(self.MORRISONS_DAILY)
                elif "Morrisons Select" in location["storeName"]:
                    item.update(self.MORRISONS_SELECT)
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif location["storeFormat"] == "pfs" and location["category"] == "Gas Station":
                item.update(self.MORRISONS)
                apply_category(Categories.FUEL_STATION, item)

            if not item.get("brand"):
                continue
            item["branch"] = item.pop("name", None)

            # Fetch store page-data.json for additional services
            page_data_url = "https://my.morrisons.com/storefinder/page-data/{}/{}/page-data.json".format(
                item["ref"], self.create_slug(location["storeName"])
            )
            yield Request(
                url=page_data_url,
                callback=self.parse_store,
                cb_kwargs={"item": item},
            )

    def parse_store(self, response, item):
        data = response.json()
        context = data["result"]["pageContext"]

        # Extract services from JSON
        services = context.get("services", [])
        service_names = [s["serviceName"] for s in services]

        has_atm = any("ATM" in service for service in service_names)
        apply_yes_no(Extras.ATM, item, has_atm)

        has_wifi = any("Wifi" in service for service in service_names)
        apply_yes_no(Extras.WIFI, item, has_wifi)

        has_baby_changing = any("Baby Changing" in service for service in service_names)
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, has_baby_changing)

        has_wheelchair = any("Disabled Access" in service for service in service_names)
        apply_yes_no(Extras.WHEELCHAIR, item, has_wheelchair)

        has_car_wash = any("Car Wash" in service for service in service_names)
        apply_yes_no(Extras.CAR_WASH, item, has_car_wash)

        has_parent_parking = any("Parent & Child Parking" in service for service in service_names)
        apply_yes_no(Extras.PARKING_PARENT, item, has_parent_parking)

        yield item

        # Extract departments (pharmacy, café) as separate POIs
        departments = context.get("departments", [])

        pharmacy_dept = next((d for d in departments if d.get("name") == "pharmacy"), None)
        if pharmacy_dept:
            pharmacy_poi = self.create_pharmacy_poi(item, pharmacy_dept)
            if pharmacy_poi:
                yield pharmacy_poi

        cafe_dept = next((d for d in departments if d.get("name") == "cafe"), None)
        if cafe_dept:
            cafe_poi = self.create_cafe_poi(item, cafe_dept)
            if cafe_poi:
                yield cafe_poi

        # Extract petrol stations from linkedLocations
        linked_locations = context.get("linkedLocations", [])
        for linked_loc in linked_locations:
            if linked_loc.get("category") == "Gas Station" and linked_loc.get("storeFormat") == "pfs":
                yield self.create_petrol_station_poi(item, linked_loc)

    def parse_opening_hours(self, opening_times_data):
        """Parse and validate opening hours from department/location data"""
        if not opening_times_data:
            return None

        # Check if hours are valid (not 00:00:00-00:00:00)
        has_valid_hours = any(
            day.get("open") != "00:00:00" or day.get("close") != "00:00:00" for day in opening_times_data
        )

        if not has_valid_hours:
            return None

        # Parse hours into OpeningHours object
        hours = OpeningHours()
        for day_hours in opening_times_data:
            hours.add_range(
                day_hours["day_short"],
                day_hours["open"],
                day_hours["close"],
                "%H:%M:%S",
            )

        return hours

    def create_department_poi(self, store_item, dept_data, poi_type, name_suffix, category):
        """Create separate POI for a department (pharmacy, café, etc.)

        Returns None if department doesn't have valid opening hours.
        """
        # Validate opening hours first
        opening_hours = self.parse_opening_hours(dept_data.get("openingTimes"))
        if not opening_hours:
            return None

        poi = store_item.copy()

        # Create unique ref
        poi["ref"] = f"{store_item['ref']}_{poi_type}"

        # Clear store-specific fields
        poi.pop("shop", None)

        # Clear store amenity extras
        if "extras" in poi:
            poi.pop("extras", None)

        # Set POI-specific fields
        apply_category(category, poi)
        poi["name"] = f"Morrisons {name_suffix}"
        poi.update(self.MORRISONS)
        poi["opening_hours"] = opening_hours

        return poi

    def create_pharmacy_poi(self, store_item, pharmacy_dept):
        """Create separate POI for pharmacy"""
        return self.create_department_poi(store_item, pharmacy_dept, "pharmacy", "Pharmacy", Categories.PHARMACY)

    def create_cafe_poi(self, store_item, cafe_dept):
        """Create separate POI for café"""
        return self.create_department_poi(store_item, cafe_dept, "cafe", "Café", Categories.CAFE)

    def create_petrol_station_poi(self, store_item, linked_loc):
        """Create separate POI for petrol station"""
        petrol = store_item.copy()

        # Use linked location's own ID and coordinates
        petrol["ref"] = str(linked_loc["name"])
        petrol["lat"] = linked_loc["location"]["latitude"]
        petrol["lon"] = linked_loc["location"]["longitude"]

        # Clear store-specific fields
        petrol.pop("shop", None)

        # Clear store amenity extras
        if "extras" in petrol:
            petrol.pop("extras", None)

        # Set petrol station-specific fields
        apply_category(Categories.FUEL_STATION, petrol)
        petrol["name"] = "Morrisons"
        petrol["branch"] = linked_loc.get("storeName", "Petrol Station")
        petrol.update(self.MORRISONS)

        # Extract opening hours
        opening_hours = self.parse_opening_hours(linked_loc.get("openingTimes"))
        if opening_hours:
            petrol["opening_hours"] = opening_hours

        return petrol
