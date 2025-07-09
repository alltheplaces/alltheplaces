
from locations.spiders.tesla import TeslaSpider

import re

import chompjs
from scrapy_zyte_api.responses import ZyteAPITextResponse

from locations.categories import Categories, apply_category

class TeslaSuperchargerSpider(TeslaSpider):
    name = "tesla_supercharger"
    item_attributes = {"brand": "Tesla Supercharger", "brand_wikidata": "Q17089620"}
    categories = ["supercharger"]



    def parse_location(self, response):
        # For some reason, the scrapy_zyte_api library doesn't detect this as a ScrapyTextResponse, so we have to do the text encoding ourselves.
        response = ZyteAPITextResponse.from_api_response(response.raw_api_response, request=response.request)

        # Many responses have false error message appended to the json data, clean them to get a proper json
        location_data = chompjs.parse_js_object(response.text)
        if isinstance(location_data, list):
            return

        feature = self.build_item(location_data)
        feature["website"] = f"https://www.tesla.com/findus/location/supercharger/{location_data.get('location_id')}".replace(" ", "")

        apply_category(Categories.CHARGING_STATION, feature)
        regex = r"(\d+) Superchargers, available 24\/7, up to (\d+kW)(<br />CCS Compatibility)?"
        regex_matches = re.findall(regex, location_data.get("chargers"))
        if regex_matches:
            for match in regex_matches:
                capacity, output, ccs_compat = match
                if ccs_compat:
                    feature["extras"]["socket:type2_combo"] = capacity
                    feature["extras"]["socket:type2_combo:output"] = output
                else:
                    feature["extras"]["socket:nacs"] = capacity
                    feature["extras"]["socket:nacs:output"] = output
        

        
        yield feature