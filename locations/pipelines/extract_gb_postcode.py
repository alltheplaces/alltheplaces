import re

from scrapy import Spider

from locations.items import Feature

GB_POSTCODE_PATTERN = re.compile(r"(\w{1,2}\d{1,2}\w? \d\w{2})")
GB_POSTCODE_0_PATTERN = re.compile(r"(\w{1,2}\d{1,2}\w?) O(\w{2})")
IE_POSTCODE_PATTERN = re.compile(r"([AC-FHKNPRTV-Y][0-9]{2}|D6W)[ -]?([0-9AC-FHKNPRTV-Y]{4})")


class ExtractGBPostcodePipeline:
    def process_item(self, item: Feature, spider: Spider | None = None) -> Feature:
        if item.get("country") == "GB":
            if item.get("addr_full") and not item.get("postcode"):
                item["postcode"] = extract_gb_postcode(item["addr_full"])
        elif item.get("country") == "IE":
            if item.get("addr_full") and not item.get("postcode"):
                if postcode := IE_POSTCODE_PATTERN.search(item["addr_full"].upper()):
                    item["postcode"] = "{} {}".format(postcode.group(1), postcode.group(2))
        return item


def extract_gb_postcode(s: str) -> str | None:
    """
    Look for first occurrence, if any, of a GB format postcode in a string.
    :param s: the string to search for a GB postcode
    :return: the first candidate postcode instance, None if not present
    """
    s = s.upper()
    if postcode := GB_POSTCODE_PATTERN.search(s):
        return postcode.group(1)
    if postcode := GB_POSTCODE_0_PATTERN.search(s):
        return postcode.group(1) + " 0" + postcode.group(2)
    return None
