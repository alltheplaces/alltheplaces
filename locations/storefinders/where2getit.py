from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.items import Feature

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

# If there are many store locations to return, it is possible the
# response will time out. If this is the case, try setting the
# value of the separate_api_call_per_country parameter to True and
# an individual request will be sent for each country, hopefully
# allowing all requests to avoid timing out. If this approach fails,
# you will need to overwrite the make_request function to use
# a more granular form of filtering (e.g. by states of a country) to
# avoid requests timing out.


class Where2GetItSpider(Spider):
    dataset_attributes = {"source": "api", "api": "where2getit.com"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    api_brand_name = ""
    api_key = ""
    api_filter = {}
    separate_api_call_per_country = False

    def make_request(self, country_code: str = None) -> JsonRequest:
        where_clause = {}
        if country_code and self.api_filter:
            where_clause = {"and": {"country": {"eq": country_code}}}
            where_clause["and"].update(self.api_filter)
        elif country_code:
            where_clause = {"country": {"eq": country_code}}
        elif self.api_filter:
            where_clause = self.api_filter
        yield JsonRequest(
            url=f"https://hosted.where2getit.com/{self.api_brand_name}/rest/getlist",
            data={
                "request": {"appkey": self.api_key, "formdata": {"objectname": "Locator::Store", "where": where_clause}}
            },
            method="POST",
            callback=self.parse_locations,
        )

    def start_requests(self):
        if self.separate_api_call_per_country:
            yield JsonRequest(
                url=f"https://hosted.where2getit.com/{self.api_brand_name}/rest/getlist",
                data={"request": {"appkey": self.api_key, "formdata": {"objectname": "Account::Country"}}},
                method="POST",
                callback=self.parse_country_list,
            )
        else:
            yield from self.make_request()

    def parse_country_list(self, response, **kwargs):
        for country in response.json()["response"]["collection"]:
            yield from self.make_request(country["name"])

    def parse_locations(self, response, **kwargs):
        for location in response.json()["response"]["collection"]:
            item = DictParser.parse(location)
            if not item["ref"]:
                item["ref"] = location["clientkey"]
            item["street_address"] = ", ".join(
                filter(None, [location.get("address1"), location.get("address2"), location.get("address3")])
            )
            yield from self.parse_item(item, location)

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
