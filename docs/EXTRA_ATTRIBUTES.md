## I found a site that gives a lot of useful, nuanced information; how do I model it in AllThePlaces?

We provide the `Extras` enum from `location.categories`, as well as the `apply_yes_no` helper.

This is great for modelling common (or even uncommon) atrributes like:

* Wheelchair accessibility
* Wifi
* Payment methods
* Fuel types
* Dietary compatibility

and more.

Example: locations/spiders/shell.py
```
from locations.categories import (
    Access,
    Categories,
    Extras,
    Fuel,
    FuelCards,
    PaymentMethods,
    apply_category,
    apply_yes_no,
)

class ShellSpider(GeoMeSpider):
    # ...
    def parse_item(self, item, location):

        amenities = location["amenities"]
        # ...
        if "restaurant" in amenities:
            apply_yes_no("food", item, True)

        if "charging" in amenities or "electric_charging_other" in fuels or "shell_recharge" in fuels:
            apply_yes_no("fuel:electricity", item, True)

        apply_yes_no(Extras.TOILETS, item, any("toilet" in a for a in amenities))
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "wheelchair_accessible_toilet" in amenities)
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "baby_change_facilities" in amenities)
        apply_yes_no(Extras.SHOWERS, item, "shower" in amenities)
        apply_yes_no(Extras.ATM, item, "atm" in amenities or "atm_in" in amenities or "atm_out" in amenities)
        apply_yes_no(
            Extras.CAR_WASH, item, any("carwash" in a for a in amenities) or any("car_wash" in a for a in amenities)
        )
```

### I have something that is a valid attribute, but there is no enum

If you have important information that isnt modelled, any valid OSM tags can be manually applied to the extras key.

Consider adding a pull request to add your enumeration value if is commonly available for your feature.

Example: Detailed wifi attributes
```
             properties = {
                "ref": location["properties"]["Name"],
                "geometry": location["geometry"],
                "name": location["properties"]["Long_Name"],
                "addr_full": location["properties"]["Location_details"],
                "extras": {
                    "internet_access": "wlan",
                    "internet_access:fee": "no",
                    "internet_access:operator": "TPG Telecom",
                    "internet_access:operator:wikidata": "Q7939276",
                    "internet_access:ssid": "VicFreeWiFi",
                },
            }
            apply_category(Categories.ANTENNA, properties)
            yield Feature(**properties)
```
