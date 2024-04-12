from itertools import chain

from scrapy import Spider

from locations.items import Feature
from locations.name_suggestion_index import NSI


class NameCleanUpPipeline:
    nsi = NSI()
    nsi_cache = {}
    strip_names = None

    def process_item(self, item: Feature, spider: Spider):
        if "branch" in item:
            return item
        if "nsi_id" not in item:
            return item

        if item["nsi_id"] not in self.nsi_cache:
            self.nsi_cache[item["nsi_id"]] = self.nsi.get_item(item["nsi_id"])

        nsi_entry = self.nsi_cache[item["nsi_id"]]
        if not nsi_entry:
            return item

        if self.strip_names is None:
            self.strip_names = getattr(spider, "strip_names", set())

        self.clean_name(nsi_entry, self.strip_names, item)

        return item

    @staticmethod
    def clean_name(nsi_entry: dict, strip_names: set[str], item: Feature):
        if not item.get("name"):
            # No name, nothing to clean
            return
        name = item["name"]
        branch = ""

        for strip_name in chain(
            strip_names,
            filter(None, [nsi_entry["tags"].get("name")]),
        ):
            if name.startswith(strip_name):
                branch = name.removeprefix(strip_name)
                break
            if name.startswith(strip_name):
                branch = name.removesuffix(strip_name)
                break

        if not branch:
            return

        item["name"] = nsi_entry.get("name")
        item["branch"] = branch.strip(" -")
