import logging
from threading import Thread
from constants import SCRAPER_TIMEOUT
import requests

logger = logging.getLogger()


class Scraper(Thread):
   def __init__(self, url_queue, result_queue, index):
      Thread.__init__(self, name='Scraper{}'.format(index))
      logging.debug('Scraper thread start!')
      self.iq = url_queue
      self.oq = result_queue

   def run(self):
      while True:

         url = self.iq.get()
         logger.debug('{} get task, qsize {}'.format(self.name, self.iq.qsize()))
         try:
            resp = requests.get(url, timeout=SCRAPER_TIMEOUT)
            if resp.status_code == 200:
               logger.debug('{} fetch successful'.format(url))
               self.oq.put(resp)
            else:
               self.iq.put(url)
               logging.error('Server returned status {}'.format(resp.status_code))
         except requests.Timeout:
            logging.error(url + ' Timeout')
            self.iq.put(url)
         except requests.RequestException as e:
            logging.error(url + ' Error')
            logger.error(e.__context__)
            self.iq.put(url)
         finally:
            self.iq.task_done()
