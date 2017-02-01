# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from scrapy.xlib.pydispatch import dispatcher
from scrapy.exceptions import DropItem
from scrapy import signals


class GeoJsonWriterPipeline(object):

    def __init__(self):
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.file = None

    def spider_opened(self, spider):
        self.file = open('{}.jl'.format(spider.name), 'wb')

    def spider_closed(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        feature = {
            "type": "Feature",
            "properties": item['properties'],
        }

        if item.get('lon_lat'):
            feature['geometry'] = {
                "type": "Point",
                "coordinates": item['lon_lat']
            }

        line = json.dumps(feature, separators=(',', ':'))
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
