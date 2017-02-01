# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from scrapy.exceptions import DropItem


class locationsPipeline(object):
    def process_item(self, item, spider):
        return item

class GeoJsonWriterPipeline(object):

    def __init__(self):
        self.file = open('items.jl', 'wb')

    def process_item(self, item, spider):
        line = json.dumps({
            "type": "Feature",
            "properties": item['properties'],
            "geometry": {
                "type": "Point",
                "coordinates": item['lon_lat']
            }
        }, separators=(',', ':'))
        self.file.write(line)
        self.file.write('\n')
        return item

class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['properties']['ref'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['properties']['ref'])
            return item
