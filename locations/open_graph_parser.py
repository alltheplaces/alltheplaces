from locations.dict_parser import DictParser
from locations.items import Feature


class OpenGraphParser:
    @staticmethod
    def parse(response) -> Feature:
        keys = response.xpath("/html/head/meta/@property").getall()
        src = {}
        for key in keys:
            if key.startswith("og:") or key.startswith("place:location:") or key.startswith("business:contact_data:"):
                content = response.xpath('//meta[@property="{}"]/@content'.format(key)).get()
                if content:
                    src[key.split(":")[-1]] = content
        item = DictParser.parse(src)
        item["website"] = response.url
        if not item.get("ref"):
            item["ref"] = response.url
        return item
