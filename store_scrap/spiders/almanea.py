from typing import Iterable
from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest, TextResponse, Request
from jsonpath_ng import parse

from store_scrap.items import Product


class AlmaneaSpider(scrapy.Spider):
    name = "almanea"
    allowed_domains = ["almanea.sa"]

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Origin": "https://www.almanea.sa",
        "Connection": "keep-alive",
        "Referer": "https://www.almanea.sa/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers"
    }

    region_id = "1116"

    cookies = {
        "__Secure-next-auth.callback-url": "https%3A%2F%2Fwww.almanea.sa%2F",
        "region_id": region_id
    }

    search_api = 'https://www.almanea.sa/api/filterSortedProducts/category'

    brand_values = {
        'Samsung': {"name": "سامسونج", "id": "117"},
        'Hisense': {"name": "هايسنس", "id": "144"},
    }

    handshake_url = 'https://www.almanea.sa/api/handshake?lang=ar'
    csrf_url = 'https://www.almanea.sa/api/auth/csrf'

    def __init__(self, brands=tuple(brand_values.keys()), **kwargs):
        super().__init__(**kwargs)
        self.brands = brands

    def get_payload(self, brand_name, brand_id, page=0):
        return {
            "url":f"facets/searchV2/{brand_name}?pageSize=20&pageNo={page}&sortBy=position&sortDir=DESC&select={self.region_id}&regionId={self.region_id}&brand={brand_id}"
        }

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            url=self.handshake_url,
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_handshake
        )

    def parse_handshake(self, response: TextResponse):
        self.cookies['handshake'] = response.json()['data']['token']
        yield Request(
            url=self.csrf_url,
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_csrf
        )

    def parse_csrf(self, response: TextResponse):
        self.cookies['__Host-next-auth.csrf-token'] = response.json()['csrfToken']
        for brand in self.brands:
            brand_id = self.brand_values[brand]['id']
            brand_name = self.brand_values[brand]['name']
            yield JsonRequest(
                url=self.search_api,
                headers=self.headers,
                cookies=self.cookies,
                data=self.get_payload(brand_name, brand_id),
                callback=self.parse,
                cb_kwargs={'brand_name': brand_name, 'brand_id': brand_id},
            )

    @staticmethod
    def get_field_value(json_data, field_name):
        return parse(f'$..{field_name}').find(json_data).pop().value


    def parse(self, response: TextResponse, brand_name, brand_id):
        json_data = response.json()
        pages = self.get_field_value(json_data, 'pages')
        current_page = self.get_field_value(json_data, 'currentpage')
        for product_data in parse('$..products[*]._source').find(json_data):
            product_data = product_data.value
            yield Product(
                name_ar=self.get_field_value(product_data, '$.name').pop(),
                price_original=self.get_field_value(product_data, 'original_price'),
                price_discounted=self.get_field_value(product_data, 'price'),
                brand_ar=self.get_field_value(product_data, 'option_text_brand').pop(),
                link=urljoin(
                    'https://www.almanea.sa/product/',
                    self.get_field_value(product_data, 'url_key').pop(),
                ),
                sku=self.get_field_value(product_data, 'sku'),
            )
        if current_page < pages:
            yield JsonRequest(
                url=self.search_api,
                headers=self.headers,
                cookies=self.cookies,
                data=self.get_payload(brand_name, brand_id, page=current_page + 1),
                callback=self.parse,
                cb_kwargs={'brand_name': brand_name, 'brand_id': brand_id},
            )
