from larkapi import RequestHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
def run():
    port = 9394
    server_address = ('', port)
    access_token = RequestHandler.get_tenant_access_token(None)
    print(access_token) 
    chatidlist = RequestHandler.getChatGroupList(None, access_token)
    for chatid in chatidlist:
        print(chatid)
#        RequestHandler.send_message(None, access_token, "", chatid, "丢你")
    httpd = HTTPServer(server_address, RequestHandler)
    print("start.....")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
