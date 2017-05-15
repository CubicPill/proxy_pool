# Proxy Pool
A simple script to fetch proxy server from websites, validate their availability and anonymity, and save to database.    
Currently supports HTTP, SOCKS4, SOCKS5     
Supports parsing websites of [cn-proxy.com](http://www.cn-proxy.com), [cnproxy.com](http://www.cnproxy.com). You can write your own parser in html_parser.py

##Validation method
Using flask web app, connect to your own server to validate the anonymity (So, your server must have a public IPv4 address).    
Can be accessed by GET http://\<your_server_ip\>:\<port\>/checkProxy    
Will return the following headers and your remote address in json format:        
```HTTP-X-VIA```   ```HTTP-X-FORWARDED-FOR```  ```HTTP-X-REAL-IP```  ```HTTP-CLIENT-IP```      
HTTPS is not supported yet, for we need a domain which has valid HTTPS certificate. All HTTPS proxy is marked as HTTP for now.

## Configuration
```ip```: Your server's public IP    
```port```: Port that flask app listen to    
```db```: Database link for sqlite3    
```url```: Proxy website urls array    
```tv```: Number of validator threads, default 32    
```ts```: Number of scraper threads, default 8    


