import scrapy

from locations.categories import Categories, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class LoewsHotelsSpider(StructuredDataSpider):
    name = "loews_hotels"
    item_attributes = {"brand": "Loews Hotels", "brand_wikidata": "Q6666622", "extras": Categories.HOTEL.value}
    allowed_domains = ["loewshotels.com"]
    start_urls = ("https://www.loewshotels.com/destinations",)
    search_for_twitter = False
    wanted_types = ["Hotel"]

    def parse(self, response):
        urls = response.xpath('//div[@class="buttons"]/a/@href').extract()
        for url in urls:
            if url.startswith("reservations.loewshotels.com"):
                pass
            elif "omni" in url:
                pass
            elif "hotel-1000" in url:
                pass
            elif "policy" in url:
                pass
            elif "mokara" in url:
                pass
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)

    def extract_amenity_features(self, item, response, ld_item):
        if "amenityFeature" in ld_item and len(ld_item["amenityFeature"]) > 0:
            if "extras" not in item:
                item["extras"] = {}

            for amenity_feature in ld_item["amenityFeature"]:
                if amenity_feature["name"] == "Number of Rooms":
                    item["extras"]["rooms"] = amenity_feature["value"]
                elif amenity_feature["name"] == "Free Wifi":
                    item["extras"]["internet_access"] = "wlan"
                    item["extras"]["internet_access:fee"]  = "no"
                elif amenity_feature["name"] == "Accessible":
                    apply_yes_no("wheelchair", item, True)
                elif amenity_feature["name"] == "Air-conditioned":
                    pass
                elif amenity_feature["name"] == "Laundry service":
                    pass
                elif amenity_feature["name"] == "Business center":
                    pass
                elif amenity_feature["name"] == "Pool":
                    apply_yes_no("swimming_pool", item, True)
                elif amenity_feature["name"] == "Pet-friendly":
                    apply_yes_no("pets_allowed", item, True)
                elif amenity_feature["name"] == "Kid-friendly":
                    pass
                elif amenity_feature["name"] == "Restaurant":
                    item["extras"]["amenity"] = "restaurant"

                elif amenity_feature["name"] == "Fitness Center":
                    item["extras"]["fitness_centre"] = "yes"

                elif amenity_feature["name"] == "Bar":
                    item["extras"]["bar"] = "yes"                
                else:
                    print(amenity_feature)
    # TODO: There are additional amenity features
    # 2024-09-28 04:18:32 [loews_hotels] DEBUG: [{'@type': 'LocationFeatureSpecification', 'value': '750', 'name': 'Number of Rooms'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Fitness Center'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'WiFi'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Outdoor Pool'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Room Service'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Restaurant'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Bar'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Valet Parking'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Parking'}, {'@type': 'LocationFeatureSpecification', 'value': True, 'name': 'Business Center'}]
