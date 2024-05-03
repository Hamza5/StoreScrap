from typing import Iterable

from scrapy import Request
from scrapy.http import HtmlResponse

from store_scrap.items import Product
from store_scrap.spiders.storescrap import StoreScrapSpider


class ZagzoogSpider(StoreScrapSpider):
    name = "zagzoog"
    allowed_domains = ["zagzoog.com"]

    brand_values = {
        'Hisense': 'هايسنس',
    }

    def start_requests(self) -> Iterable[Request]:
        for brand in self.brands:
            if brand in self.brand_values:
                yield Request(
                    url=f'https://zagzoog.com/arabic/ajax_products.php?s=all&c=&min_price=0&max_price=30000&orderby=&brand={brand}&type=&searchh=&display_mode=grid',
                    callback=self.parse
                )

    def parse(self, response: HtmlResponse) -> Iterable[Product | Request]:
        for product_div in response.css('.product'):
            name = product_div.css('.name a::text').get()
            link = response.urljoin(product_div.css('.name a::attr(href)').get())
            original_price = product_div.css('.price del ::text').get('').split(' ')[0]
            discounted_price = product_div.css('.price ins ::text').get('').split(' ')[0]
            model_code = product_div.css('h3+div::text').get().split('-')[0].strip()
            yield Product(
                name_ar=name,
                price_original=float(original_price) if original_price else '',
                price_discounted=float(discounted_price) if discounted_price else '',
                link=link,
                sku=model_code
            )
