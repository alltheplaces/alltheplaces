import re


class ExtractGBPostcodePipeline:
    def process_item(self, item, spider):
        if item.get("country") == "GB":
            if item.get("addr_full") and not item.get("postcode"):
                item["postcode"] = extract_gb_postcode(item["addr_full"])
        elif item.get("country") == "IE":
            if item.get("addr_full") and not item.get("postcode"):
                if postcode := re.search(
                    r"([AC-FHKNPRTV-Y][0-9]{2}|D6W)[ -]?([0-9AC-FHKNPRTV-Y]{4})", item["addr_full"].upper()
                ):
                    item["postcode"] = "{} {}".format(postcode.group(1), postcode.group(2))
        return item


def extract_gb_postcode(s: str):
    """
    Look for first occurrence, if any, of a GB format postcode in a string.
    :param s: the string to search for a GB postcode
    :return: the first candidate postcode instance, None if not present
    """
    s = s.upper()
    if postcode := re.search(r"(\w{1,2}\d{1,2}\w? \d\w{2})", s):
        return postcode.group(1)
    if postcode := re.search(r"(\w{1,2}\d{1,2}\w?) O(\w{2})", s):
        return postcode.group(1) + " 0" + postcode.group(2)
    return None
