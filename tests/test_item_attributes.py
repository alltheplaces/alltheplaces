from scrapy.utils.misc import walk_modules
from scrapy.utils.spider import iter_spider_classes

from locations.settings import SPIDER_MODULES


def test_item_attributes_type():
    for mod in SPIDER_MODULES:
        for module in walk_modules(mod):
            for spider_class in iter_spider_classes(module):
                item_attributes = getattr(spider_class, "item_attributes", {})
                assert isinstance(item_attributes, dict)

                if extras := item_attributes.get("extras"):
                    assert isinstance(extras, dict)
