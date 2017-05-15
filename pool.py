import json
import logging
import time
from _thread import start_new_thread
from queue import Queue
from threading import Thread

from db import save_proxy_servers, UpdateValidateResult, db_query_all_alive_and_put, init_db
from html_parser import parse
from scraper import Scraper
from validate import anonymity_checker_app, ProxyServerValidator

url_queue = Queue()
parser_queue = Queue()
db_save_queue = Queue()
db_update_queue = Queue()
db_query_result_queue = Queue()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(name)s %(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)


class ValidateServerThread(Thread):
   def __init__(self):
      Thread.__init__(self, name='ValidateServerThread')

   def run(self):
      logger.info('Operation start')
      db_query_all_alive_and_put(db_query_result_queue)
      updater = UpdateValidateResult(db_update_queue)
      updater.start()
      # wait for validator thread to finish job
      db_query_result_queue.join()
      db_update_queue.put('exit')  # terminate this thread
      logger.info('Sleep')


class FetchServerThread(Thread):
   def __init__(self, url_list):
      Thread.__init__(self, name='FetchServerThread')
      self.url_list = url_list

   def run(self):
      logger.info('Operation start')
      for url in self.url_list:
         url_queue.put(url)
      url_queue.join()
      parse_result = parse(parser_queue)
      save_proxy_servers(parse_result)
      logger.info('Sleep')


def run_validate_every_interval(interval):
   while True:
      ValidateServerThread().start()
      time.sleep(interval)


def run_fetch_every_interval(url_list, interval):
   while True:
      FetchServerThread(url_list).start()
      time.sleep(interval)


def main():
   with open('config.json') as f:
      config = json.load(f)
   init_db(config['db'])
   start_new_thread(anonymity_checker_app.run, ('0.0.0.0', config['port']))
   validator_thread_pool = list()
   for i in range(config['tv']):
      validator = ProxyServerValidator(config['ip'], config['port'], db_query_result_queue, db_update_queue, i)
      validator.start()
      validator_thread_pool.append(validator)

   thread_pool = list()
   for i in range(config['ts']):
      scraper = Scraper(url_queue, parser_queue, i)
      scraper.start()
      thread_pool.append(scraper)

   start_new_thread(run_fetch_every_interval, (config['url'], 7200))
   start_new_thread(run_validate_every_interval, (3600,))
   logger.info('Main thread exit')


if __name__ == '__main__':
   main()
