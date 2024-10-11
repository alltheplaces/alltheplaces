## I found a site that gives a lot of useful, nuanced information; how do I model it in AllThePlaces?

We provide the `Extras` enum from `location.categories`, as well as the `apply_yes_no` helper.

This is great for modelling common (or even uncommon) atrributes like:

* Wheelchair accessibility
* Wifi
* Payment methods
* Fuel types
* Dietary compatibility

and more.

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
