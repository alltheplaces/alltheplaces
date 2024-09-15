from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.items import Feature


class JSONBlobSpider(Spider):
    """
    A JSONBlobSpider is a lightweight spider for extracting features from a
    single JSON response returned from a specified `start_urls[0]`, or
    alternatively for extracting features from a JavaScript object nested in
    a HTML response for a specified `start_urls[0]`.

    To use this spider, specify a URL with `start_urls`.

    If a JSON response is received, three options then need to be considered:
    1. If the JSON response is a dictionary of features:
        a. Overload the `pre_process_data` and/or `post_process_item`
           functions to adjust feature attributes before and/or after
           `DictParser` has been used to automatically extract the feature.
        b. Note that the dictionary key will be added as a new attribute
           `feature_id` in the dictionary that is provided to
           `pre_process_data` and `post_process_item` functions.
    2. If the JSON response is an array of features, overload the
       `pre_process_data` and/or `post_process_item` functions to adjust
       feature attributes before and/or after `DictParser` has been used to
       automatically extract the feature.
    3. If the JSON response is more complex, for example, a nested tree of
       dictionaries and arrays followed by an array of features, overload
       the `parse` function to obtain the required dictionary or array of
       features which can then be passed to `parse_feature_dict` or
       `parse_feature_array` functions.

    If a HTML response is received, the `extract_json` function will need to
    be overloaded to extract a JavaScript script from within the HTML response
    and extract a JSON dictionary or array from within the JavaScript script.
    This may typically include use of `json.loads` or
    `chompjs.parse_js_object`. Once a dictionary or array of features has been
    extracted from the HTML response with `extract_json`, it is then handled
    in the same way as if a JSON response rather than HTML response had been
    received.
    """

    """
    locations_key:
    If set then use as a key into the JSON response to return the location
    data array. This can either be specified as a single string if a single
    dictionary contains the location data array, or as an ordered list of
    strings if a nested set of dictionaries exists.
    
    Example 1:
    locations_key = "data"

    Example 2:
    locations_key = ["data", "locationData", "stores"]
    """
    locations_key: str | list[str] = None

    def extract_json(self, response: Response) -> dict | list:
        """
        Override this method to extract the main JSON content from the page. The default
        behaviour is to treat the returned body as JSON and treat it as an array of
        locations to be given to DictParser.

        Example 1:
        data_raw = response.xpath("//div[@id='content']/script/text()").get()
        data_raw = data_raw.replace("pageData.push({ stores: ", "").replace("});", "")
        features_dict = json.loads(data_raw)
        return features_dict

        Example 2:
        data_raw = response.xpath("//script[contains(text(), '},\"places\":[{')]/text()").get()
        data_raw = data_raw.split('},"places":', 1)[1]
        features_dict = chompjs.parse_js_object(data_raw)
        return features_dict
        """
        json_data = response.json()
        if self.locations_key:
            if isinstance(self.locations_key, str):
                json_data = json_data[self.locations_key]
            elif isinstance(self.locations_key, list):
                for key in self.locations_key:
                    json_data = json_data[key]
        return json_data

    def parse(self, response: Response) -> Iterable[Feature]:
        features = self.extract_json(response)
        if isinstance(features, dict):
            yield from self.parse_feature_dict(response, features) or []
        else:
            yield from self.parse_feature_array(response, features) or []

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature) or []

    def parse_feature_dict(self, response: Response, feature_dict: dict) -> Iterable[Feature]:
        for feature_id, feature in feature_dict.items():
            if not feature.get("id"):
                feature["id"] = feature_id
            else:
                feature["feature_id"] = feature_id
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature) or []

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the data, ie normalising key names for DictParser."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override ith any post process on the item"""
        yield item
