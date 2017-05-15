import logging
import time
from threading import Thread

from sqlalchemy import create_engine, types, Column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from constants import Anonymity

engine = None
logger = logging.getLogger()
BaseDBModel = declarative_base(bind=engine)


def init_db(db_link):
   logger.debug('db init')
   global engine
   engine = create_engine(db_link, connect_args={'check_same_thread': False}, echo=False)
   BaseDBModel.metadata.create_all(bind=engine)


class ProxyDBModel(BaseDBModel):
   __tablename__ = 'proxy'
   ip = Column(types.String, primary_key=True)
   port = Column(types.String, nullable=False)
   location = Column(types.String, default='Unknown')
   latency = Column(types.Float, default=-1)
   anonymity = Column(types.String, default=Anonymity.Unknown)
   type = Column(types.String, nullable=False)
   online = Column(types.Boolean, default=False)
   fail_times = Column(types.Integer, default=0)
   dead_flag = Column(types.Boolean, default=False)
   update_time = Column(types.DateTime)

   def __repr__(self):
      return '<ProxyServer(ip={ip}, port={port})>'.format(ip=self.ip, port=self.port)


def save_proxy_servers(dict_list):
   count = 0
   fail = 0
   dup = 0
   session = scoped_session(sessionmaker(bind=engine))()
   for item in dict_list:
      if not session.query(ProxyDBModel).filter_by(ip=item['ip']).first():
         logger.debug('Saving {}'.format(item))
         orm = _parse_dict(item)
         try:
            _insert_db(session, orm)
            count += 1
         except IntegrityError as e:
            logger.error(e.__str__())
            fail += 1
            session.rollback()
      else:
         logger.debug('IP {} already exists, pass'.format(item['ip']))
         dup += 1
   logger.info('Saving done, {} success, {} fails, {} duplicates'.format(count, fail, dup))


def _parse_dict(_dict):
   ip = _dict.get('ip')
   port = _dict.get('port')
   location = _dict.get('location')
   _type = _dict.get('type')
   update_time = _dict.get('update_time')
   return ProxyDBModel(ip=ip, port=port, location=location, type=_type, update_time=update_time)


def _insert_db(session, orm):
   # data should be an orm obj
   session.add(orm)
   session.commit()


class UpdateValidateResult(Thread):
   def __init__(self, update_queue):
      Thread.__init__(self, name='UpdateValidateResult')
      self.iq = update_queue

   def run(self):
      online = 0
      offline = 0
      while True:
         if not self.iq.empty():
            _dict = self.iq.get_nowait()
            if _dict == 'exit':
               logger.debug('Thread exit')
               break
            if _dict['online']:
               online += 1
            else:
               offline += 1
            _update_or_delete(_dict)
            self.iq.task_done()
         else:
            time.sleep(1)
      logger.info('Validate result updating done, {} online, {} offline'.format(online, offline))


def _update_or_delete(_dict):
   session = scoped_session(sessionmaker(bind=engine))()
   session.query(ProxyDBModel).filter_by(ip=_dict['ip']).update(_dict)
   session.commit()
   logger.debug('Updated ip {}'.format(_dict['ip']))


def db_query_all_alive_and_put(queue):
   session = scoped_session(sessionmaker(bind=engine))()
   cursor = session.query(ProxyDBModel).filter_by(dead_flag=False)
   logger.info('{} alive servers in database'.format(cursor.count()))

   for record in cursor:
      queue.put(record)
   session.close()
