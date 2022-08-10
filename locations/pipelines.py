# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re

from scrapy.exceptions import DropItem


class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        ref = (spider.name, item["ref"])
        if ref in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(ref)
            return item


class ApplySpiderNamePipeline(object):
    def process_item(self, item, spider):
        existing_extras = item.get("extras", {})
        existing_extras["@spider"] = spider.name
        item["extras"] = existing_extras

        return item


class ApplySpiderLevelAttributesPipeline(object):
    def process_item(self, item, spider):
        if not hasattr(spider, "item_attributes"):
            return item

        item_attributes = spider.item_attributes

        for (key, value) in item_attributes.items():
            if item.get(key) is None:
                item[key] = value

        return item


class ExtractGBPostcodePipeline(object):
    def process_item(self, item, spider):
        if item.get("country") == "GB":
            if item.get("addr_full") and not item.get("postcode"):
                postcode = re.search(
                    r"(\w{1,2}\d{1,2}\w? \d\w{2})", item["addr_full"].upper()
                )
                if postcode:
                    item["postcode"] = postcode.group(1)
                else:
                    postcode = re.search(
                        r"(\w{1,2}\d{1,2}\w?) O(\w{2})", item["addr_full"].upper()
                    )
                    if postcode:
                        item["postcode"] = postcode.group(1) + " 0" + postcode.group(2)

        return item


class AssertURLSchemePipeline(object):
    def process_item(self, item, spider):
        if item.get("image"):
            if item["image"].startswith("//"):
                item["image"] = "https:" + item["image"]

        return item
