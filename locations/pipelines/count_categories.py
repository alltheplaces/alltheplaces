from locations.categories import get_category_tags


class CountCategoriesPipeline:
    def process_item(self, item, spider):
        if categories := get_category_tags(item):
            for k, v in sorted(categories.items()):
                spider.crawler.stats.inc_value("atp/category/%s/%s" % (k, v))
                break
            if len(categories) > 1:
                spider.crawler.stats.inc_value("atp/category/multiple")
        else:
            spider.crawler.stats.inc_value("atp/category/missing")
        return item
