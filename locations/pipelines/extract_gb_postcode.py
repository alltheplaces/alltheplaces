import re


class ExtractGBPostcodePipeline:
    def process_item(self, item, spider):
        if item.get("country") == "GB":
            if item.get("addr_full") and not item.get("postcode"):
                postcode = re.search(r"(\w{1,2}\d{1,2}\w? \d\w{2})", item["addr_full"].upper())
                if postcode:
                    item["postcode"] = postcode.group(1)
                else:
                    postcode = re.search(r"(\w{1,2}\d{1,2}\w?) O(\w{2})", item["addr_full"].upper())
                    if postcode:
                        item["postcode"] = postcode.group(1) + " 0" + postcode.group(2)
        elif item.get("country") == "IE":
            if item.get("addr_full") and not item.get("postcode"):
                if postcode := re.search(
                    r"([AC-FHKNPRTV-Y][0-9]{2}|D6W)[ -]?([0-9AC-FHKNPRTV-Y]{4})", item["addr_full"].upper()
                ):
                    item["postcode"] = "{} {}".format(postcode.group(1), postcode.group(2))

        return item
