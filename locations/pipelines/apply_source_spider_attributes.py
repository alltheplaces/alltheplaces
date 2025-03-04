from inspect import getmro

from scrapy.utils.trackref import object_ref


class ApplySourceSpiderAttributesPipeline:
    def process_item(self, item, spider):
        existing_extras = item.get("extras", {})
        existing_extras["@spider"] = spider.name
        spider_classes = getmro(type(spider))
        spider_classes = tuple(filter(lambda x: x != object_ref and x != object, spider_classes))
        existing_extras["@spider_classes"] = spider_classes
        item["extras"] = existing_extras
        return item
