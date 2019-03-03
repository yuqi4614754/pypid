# encoding:utf-8
# !/usr/bin/env python
import psutil
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

# 后台线程 产生数据，即刻推送至前端
def query_pid_info(pid):
    p = psutil.Process(pid)
    app.logger.debug("query start!")
    timeInfo = time.strftime('%M:%S', time.localtime())
    # 获取系统时间（只取分:秒）
    tmp = p.cpu_percent(interval=1)
    cpuInfo = (tmp,)
    tmp = p.memory_info()
    memInfo = (tmp.rss/1024, tmp.vms/1024, tmp.shared/1024, tmp.text/1024, tmp.lib/1024, tmp.data/1024, tmp.dirty/1024)
    tmp = p.io_counters()
    ioInfo = (tmp.read_bytes/1024,tmp.write_bytes/1024,tmp.read_count,tmp.write_count)
    tmp = p.io_counters()
    statInfo = (p.num_threads(), p.num_fds())
    # 获取系统cpu使用率 non-blocking
    socketio.emit('my_response', {'time': timeInfo, 'cpu': cpuInfo, 'mem': memInfo, 'io': ioInfo , 'stat' : statInfo}, namespace='/test')
    # 注意：这里不需要客户端连接的上下文，默认 broadcast = True

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('connect', namespace='/test')
def test_connect():
    app.logger.debug('connect')

@socketio.on('my_event', namespace='/test')
def host_info(message):
    app.logger.debug("receive data: %s" %message)
    pid = int(message['data'])
    if psutil.pid_exists(pid):
        query_pid_info(pid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)
