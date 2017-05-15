REGEX_IP = '(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}' \
           '(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
SCRAPER_TIMEOUT = 10


class ProxyType:
   SOCKS5 = 'SOCKS5'
   SOCKS4 = 'SOCKS4'
   HTTP = 'HTTP'
   HTTPS = 'HTTP'
   # skipping HTTPS for now, for we need a domain with SSL to verify it


class Anonymity:
   Unknown = 'Unknown'
   Transparent = 'Transparent'
   Anonymous = 'Anonymous'
   Highly_anonymous = 'Highly_anonymous'
