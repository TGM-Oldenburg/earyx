from tornado.websocket import WebSocketHandler
from tornado.web import Application
from tornado.ioloop import IOLoop
import json


class EchoWebSocket(WebSocketHandler):
    answer = 0
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + str(json.loads(message)['content']))
        print("U said " + str(json.loads(message)['content']))
        self.answer = json.loads(message)['content']
              
    def on_close(self):
        print("WebSocket closed")

    def check_origin(self, origin):
        return True

    def start_web():
        app = Application([("/test", EchoWebSocket)])
        port = 8888
        app.listen(port)
        IOLoop.instance().start()
