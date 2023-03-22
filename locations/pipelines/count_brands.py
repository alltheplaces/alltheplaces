class CountBrandsPipeline:
    def process_item(self, item, spider):
        if brand := item.get("brand"):
            spider.crawler.stats.inc_value(f"atp/brand/{brand}")
        if wikidata := item.get("brand_wikidata"):
            spider.crawler.stats.inc_value(f"atp/brand_wikidata/{wikidata}")
        return item
