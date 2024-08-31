from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


# A JSONBlobSpider is a lightweight spider for sites embedding a JS/JSON array of hashes
# embedded in a single page.
#
# To use, implement an `extract_json` method to locate and parse your JSON data;
# `pre_process_data` to clean up the keys of an individual entry; and
# `post_process_item` to apply any further attributes
class JSONBlobSpider(Spider):
    """
    Provide some lightweight support for iterating an array of JSON POI locations
    and passing each entry to DictParser. Hooks are provided such that subclasses
    can override the logic at various stages of the pipeline.
    """

    # If set then use as a key into the JSON response to return the location data array.
    locations_key: str = None

    def extract_json(self, response: Response):
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
            return json_data[self.locations_key]
        return json_data

    def parse(self, response: Response, **kwargs):
        features = self.extract_json(response)
        if isinstance(features, dict):
            yield from self.parse_feature_dict(response, features) or []
        else:
            yield from self.parse_feature_array(response, features) or []

    def parse_feature_array(self, response: Response, feature_array: list, **kwargs):
        for feature in feature_array:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature) or []

    def parse_feature_dict(self, response: Response, feature_dict: dict, **kwargs):
        for feature_id, feature in feature_dict.items():
            if not feature.get("id"):
                feature["id"] = feature_id
            else:
                feature["feature_id"] = feature_id
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature) or []

    def pre_process_data(self, feature, **kwargs):
        """Override with any pre-processing on the data, ie normalising key names for DictParser."""

    def post_process_item(self, item, response: Response, feature: dict):
        """Override ith any post process on the item"""
        yield item
