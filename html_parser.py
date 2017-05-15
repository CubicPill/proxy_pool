import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup

from constants import ProxyType, REGEX_IP

logger = logging.getLogger()


def parse(parse_queue):
   result = list()
   count = 0
   while not parse_queue.empty():
      item = parse_queue.get_nowait()
      count += 1
      soup = BeautifulSoup(item.content, 'html5lib')
      result.extend(_parse(item.url, soup))
   logger.debug('Queue parse done, {}urls, {} items'.format(count, len(result)))
   return result


def _parse(url, soup):
   result = []

   def parse_cn_proxy():
      result_arr = []
      table_rows = soup.find_all('tr')
      for row in table_rows:

         item_list = row.find_all('td')
         if len(item_list) == 5:
            ip = item_list[0].text
            if not re.match(REGEX_IP + '$', ip):
               continue
            port = item_list[1].text
            location = item_list[2].text
            result_arr.append({
               'ip': ip,
               'port': port,
               'location': location,
               'type': ProxyType.HTTP,
               'update_time': datetime.now()
            })

      return result_arr

   def parse_cnproxy():
      result_arr = []
      kv_str = soup.script.text[1:-1].replace('"', '').split(';')
      kv_dict = dict()
      for item in kv_str:
         k = item.split('=')[0]
         v = item.split('=')[1]
         kv_dict[k] = v

      table_rows = soup.find_all('tr')
      for row in table_rows:
         item_list = row.find_all('td')
         ip_port = item_list[0].text
         match = re.match('({})document\.write\(":"\+(.*)\)'.format(REGEX_IP), ip_port)
         if not match:
            continue

         ip = match.group(1)
         port_str = match.group(2).split('+')
         port = ''
         for letter in port_str:
            port += kv_dict[letter]
         _type = ProxyType.HTTP
         if item_list[1].text == 'HTTP':
            _type = ProxyType.HTTP
         elif item_list[1].text == 'SOCKS4':
            _type = ProxyType.SOCKS4
         elif item_list[1].text == 'SOCKS5':
            _type = ProxyType.SOCKS5

         location = item_list[3].text
         result_arr.append({
            'ip': ip,
            'port': port,
            'location': location,
            'type': _type,
            'update_time': datetime.now()
         })
      return result_arr

   if 'http://cn-proxy.com' in url:
      result = parse_cn_proxy()
   elif 'http://www.cnproxy.com' in url:
      result = parse_cnproxy()
   else:
      pass

   return result
