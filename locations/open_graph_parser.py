from locations.dict_parser import DictParser
from locations.items import Feature

KNOWN_PREFIXES = ["og:", "place:location:", "business:contact_data:"]


class OpenGraphParser:
    def extract_properties(self, response):
        keys = response.xpath("/html/head/meta/@property").getall()
        src = {}
        for key in keys:
            for known_prefix in KNOWN_PREFIXES:
                if key.startswith(known_prefix):
                    if content := response.xpath('//meta[@property="{}"]/@content'.format(key)).get():
                        src[key.split(known_prefix)[-1]] = content
                        # No need to look at other KNOWN_PREFIXES
                        break
        return src

    def as_item(self, properties, response):
        item = DictParser.parse(properties)
        item["website"] = response.url
        if not item.get("ref"):
            item["ref"] = response.url
        return item

    @staticmethod
    def parse(response) -> Feature:
        og = OpenGraphParser()
        return og.as_item(og.extract_properties(response), response)
