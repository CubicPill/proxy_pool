import json
import logging
import time
from datetime import datetime
from threading import Thread

import requests
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

from constants import Anonymity

logger = logging.getLogger()
anonymity_checker_app = Flask(__name__)


@anonymity_checker_app.route('/checkProxy', methods=['GET'])
def return_related_headers():
   http_x_via = request.headers.get('X_VIA')
   http_x_forwarded_for = request.headers.get('X_FORWARDED_FOR')
   http_x_real_ip = request.headers.get('X_REAL_IP')
   http_client_ip = request.headers.get('CLIENT_IP')
   return jsonify({
      'success': True,
      'remote_addr': request.remote_addr,
      'http_x_via': http_x_via,
      'http_x_forwarded_for': http_x_forwarded_for,
      'http_x_real_ip': http_x_real_ip,
      'http_client_ip': http_client_ip
   })


@anonymity_checker_app.errorhandler(BadRequest)
def handle_bad_request(e):
   return jsonify({
      'success': False,
      'error': 'Bad request'
   })


class ProxyServerValidator(Thread):
   def __init__(self, host_ip, host_port, proxy_queue, result_queue, index):
      Thread.__init__(self, name='Validator{}'.format(index))
      self.host_ip = host_ip
      self.host_port = host_port
      self.iq = proxy_queue
      self.oq = result_queue

   def run(self):
      while True:
         obj = self.iq.get()
         logger.debug('Get {}, queue size: {}'.format(obj.ip, self.iq.qsize()))
         proxy_ip, proxy_port, fail_times, _type = obj.ip, obj.port, obj.fail_times, obj.type
         try:
            latency, anonymity = self.check(self.host_ip, self.host_port, proxy_ip, proxy_port, _type)
            _dict = {
               'ip': proxy_ip,
               'latency': latency,
               'anonymity': anonymity,
               'online': True if latency > 0 else False,
               'fail_times': 0 if latency > 0 else fail_times + 1,
               'dead_flag': True if fail_times + 1 >= 3 else False,
               'update_time': datetime.now()
            }
            if _dict['dead_flag']:
               logger.info('Set dead flag to ip {} for too many connection failures'.format(_dict['ip']))
            self.oq.put(_dict)
            logger.debug('{} validating done'.format(proxy_ip))
            logger.debug(_dict)
         except Exception as e:
            logger.error(e.__context__)
         finally:
            self.iq.task_done()

   @staticmethod
   def check(host_ip, host_port, proxy_ip, proxy_port, proxy_type):
      try:
         start_time = time.time()
         resp = requests.get('http://{}:{}/checkProxy'.format(host_ip, host_port),
                             proxies={'http': '{type}://{ip}:{port}'.format(type=proxy_type.lower(),
                                                                            ip=proxy_ip, port=proxy_port)}, timeout=30)
         if resp.status_code != 200:
            return -1, Anonymity.Unknown
         info = resp.json()
         latency = round((time.time() - start_time) * 1e3)
      except Exception as e:
         logger.debug(e.__context__)
         return -1, Anonymity.Unknown
      if not info['success']:
         return -1, Anonymity.Unknown
      if host_ip in json.dumps(info):
         anonymity = Anonymity.Transparent
      elif info['http_x_via'] or info['http_x_forwarded_for']:
         anonymity = Anonymity.Anonymous
      elif not info['http_x_forwarded_for'] and not info['http_x_via'] and not info['http_x_real_ip'] and not info[
         'http_client_ip']:
         anonymity = Anonymity.Highly_anonymous
      else:
         anonymity = Anonymity.Unknown
      return latency, anonymity
