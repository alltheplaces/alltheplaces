from scrapy import Spider

from locations.dict_parser import DictParser


# A JSONBlobSpider is a lightweight spider for sites embedding a JS/JSON array of hashes
# embedded in a single page.
#
# To use, implement an `extract_json` method to locate and parse your JSON data;
# `pre_process_data` to clean up the keys of an individual entry; and
# `post_process_item` to apply any further attributes
class JSONBlobSpider(Spider):
    def extract_json(response):
        """
        Override this method to extract the main JSON content from the page.

        Example 1:
        raw = response.xpath("//div[@id='content']/script/text()").extract_first()
        raw = raw.replace("pageData.push({ stores: ", "").replace("});", "")
        stores_json = json.loads(raw)
        return stores_json

        Example 2:
        data_raw = response.xpath("//script[contains(text(), '},\"places\":[{')]/text()").get()
        data_raw = data_raw.split('},"places":', 1)[1]
        locations = chompjs.parse_js_object(data_raw)
        """

    def parse(self, response, **kwargs):
        locations = self.extract_json(response)

        for location in locations:
            self.pre_process_data(location)
            item = DictParser.parse(location)
            yield from self.post_process_item(item, response, location) or []

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the data, ie normalising key names for DictParser."""

    def post_process_item(self, item, response, location):
        """Override ith any post process on the item"""
        yield item
