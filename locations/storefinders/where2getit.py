import pycountry
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

# To use this storefinder, supply an api_brand_name value as would
# be found in the following URL template:
# https://hosted.where2getit.com/{api_brand_name}/rest/...
# The api_key value needs to be supplied too and is found in the
# request parameters for a POST to this URL. It is formatted as a
# UUID (https://en.wikipedia.org/wiki/Universally_unique_identifier).

# The api_filter value is optional and allows server-side
# filtering of store locations which will be returned. This is useful
# for spiders where you may want to only return official stores and
# not resellers of a brand's products. It is also useful for
# filtering out new stores not yet open, or stores which are closed
# but which haven't been removed from the database.

# Filters are a dictionary of nested rules that can include the
# following types of rules:
# * and     - all nested rules must return true
# * or      - at least one nested rule must return true
# * like    - a string must contain the specified string
#             (case sensitive)
# * ilike   - a string must contain the specified string
#           (case insensitive)
# * notlike - a string must not contain the specified string
# * in      - a string must match one of the strings specified in a
#             comma-separated list
# * notin   - a string must not match any of the strings specified
#             in a comma-separated list
# * eq      - a string must equal the specified string
# * ne      - a string must not equal the specified string
# * gt      - a number must be greater than the specified number
# * lt      - a number must be less than the specified number
# * ge      - a number must be greater than or equal to the specified
#             number
# * le      - a number must be less than or equal to the specified
#             number
# * between - a number must be between (including lower and upper
#             bounds) the number range specified as a
#             comma-separated list
#
# As an example:
# {"or": {"field1": {"in", "value1,value2,value3"},
#         "field2": {"eq", "value4"}
#        }
# }
#
# As filters are complex to understand, it is best to search spiders
# using "api_query" to see other examples of filters being used.

# Instead of Where2GetIt being provided as a service, it is also
# possible for brands to self-host the software at a custom domain
# name. If this is the case, change the api_endpoint value to be
# the custom API url ending in "/rest/getlist".

# If there are many store locations to return, it is possible the
# response will time out. If this is the case, try setting the
# value of the api_filter_admin_level to 1 for querying results
# country-by-country. If timeouts still occur, set
# api_filter_admin_level to 2 for querying results not just by
# country, but also state-by-state or province-by-province. If you
# still experience timeouts, you will need to overwrite the
# make_request function to use a more granular form of querying, for
# example, by city of each location.


class Where2GetItSpider(Spider):
    dataset_attributes = {"source": "api", "api": "where2getit.com"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    api_endpoint: str = ""
    api_brand_name: str = ""
    api_key: str = ""
    api_filter: dict = {}
    # api_filter_admin_level:
    #   0 = no filtering
    #   1 = filter by country
    #   2 = filter by state/province
    api_filter_admin_level: int = 0

    def make_request(self, country_code: str = None, state_code: str = None, province_code: str = None) -> JsonRequest:
        where_clause = {}
        location_clause = {}
        if country_code:
            if state_code:
                location_clause = {
                    "and": {
                        "country": {"eq": country_code},
                        "state": {"eq": state_code},
                    }
                }
            elif province_code:
                location_clause = {
                    "and": {
                        "country": {"eq": country_code},
                        "province": {"eq": province_code},
                    }
                }
            else:
                location_clause = {"country": {"eq": country_code}}
        if self.api_filter:
            where_clause = {"and": self.api_filter | location_clause}
        else:
            where_clause = location_clause

        url = f"https://hosted.where2getit.com/{self.api_brand_name}/rest/getlist"
        if self.api_endpoint:
            url = self.api_endpoint
        yield JsonRequest(
            url=url,
            data={
                "request": {"appkey": self.api_key, "formdata": {"objectname": "Locator::Store", "where": where_clause}}
            },
            method="POST",
            callback=self.parse_locations,
            dont_filter=True,
        )

    def start_requests(self):
        if self.api_filter_admin_level > 0:
            url = f"https://hosted.where2getit.com/{self.api_brand_name}/rest/getlist"
            if self.api_endpoint:
                url = self.api_endpoint
            yield JsonRequest(
                url=url,
                data={"request": {"appkey": self.api_key, "formdata": {"objectname": "Account::Country"}}},
                method="POST",
                callback=self.parse_country_list,
                dont_filter=True,
            )
        else:
            yield from self.make_request()

    def parse_country_list(self, response, **kwargs):
        for country in response.json()["response"]["collection"]:
            country_code = country["name"]
            subdivisions = pycountry.subdivisions.get(country_code=country_code)
            if self.api_filter_admin_level > 1 and subdivisions:
                for state in subdivisions:
                    state_code = state.code[-2:]
                    if state.type == "Province":
                        yield from self.make_request(country_code=country_code, province_code=state_code)
                    else:
                        yield from self.make_request(country_code=country_code, state_code=state_code)
            else:
                yield from self.make_request(country_code=country_code)

    def parse_locations(self, response, **kwargs):
        if response.json().get("code") and response.json()["code"] == 5007:
            # No results returned for the provided API filter.
            return
        for location in response.json()["response"]["collection"]:
            item = DictParser.parse(location)
            if not item["ref"]:
                item["ref"] = location["clientkey"]
            item["street_address"] = clean_address(
                [location.get("address1"), location.get("address2"), location.get("address3")]
            )
            yield from self.parse_item(item, location)

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
