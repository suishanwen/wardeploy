import os
import time
import datetime
import pytz
from file_read_backwards import FileReadBackwards
from Logger import logger
from StaticLoader import STATIC_LOADER

locker = {
    "9093": False,
    "9193": False,
    "9293": False,
    "9393": False
}

package_name = "OES"


def get_log(file, un_reverse=True, size=1000):
    with FileReadBackwards(file, encoding="utf-8") as frb:
        lines = []
        while len(lines) < size:
            line = frb.readline()
            if not line:
                break
            lines.append(line)
    if un_reverse:
        lines = lines[::-1]
    return "<br/>".join(lines)


def hello(_, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    yield STATIC_LOADER["app/index.html"].encode('utf-8')


def upload(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    params = environ['params']
    port = params.get('tomcat')
    if locker[port]:
        result = f"{port}当前正在处理锁定中,请稍后再试"
    else:
        locker[port] = True
        try:
            tomcat = f"/data/tomcat7_finance_{port}"
            name = params.get("name")
            file = params.get("file")
            with open(f"file/{port}/{name}", 'wb') as f:
                f.write(file)
            shutdown(port)
            unzip(port, name)
            rm(tomcat)
            mv(tomcat, port)
            cp(tomcat)
            start(tomcat)
            result = "替包成功"
        except Exception as e:
            logger.error(str(e))
            result = f"替包:{str(e)}"
        finally:
            locker[port] = False
    write_log(port, result)
    yield result.encode('utf-8')


def shell(cmd):
    logger.info(cmd)
    os.system(cmd)


def unzip(port, file_name):
    cmd = f"""cd /data/wardeploy/file/{port}
    rm -rf mvcost
    unzip {file_name}"""
    shell(cmd)


def rm(tomcat):
    cmd = f"rm -rf {tomcat}/webapps/finance"
    shell(cmd)
    cmd = f"rm -rf {tomcat}/webapps/{package_name}"
    shell(cmd)


def mv(tomcat, port):
    cmd = f"mv /data/wardeploy/file/{port}/mvcost {tomcat}/webapps/{package_name}"
    shell(cmd)


def cp(tomcat):
    cmd0 = f"rm -rf {tomcat}/webapps/WEB-INF/application.properties"
    cmd = f"cp {tomcat}/webapps/application.properties {tomcat}/webapps/{package_name}/WEB-INF/application.properties"
    shell(cmd0)
    shell(cmd)


def shutdown(port):
    cmd = "ps -ef | grep tomcat7_finance_" + port + " | grep -v grep | awk '{print $2}' | xargs kill -9"
    shell(cmd)


def start(tomcat):
    cmd = f"""cd {tomcat}/bin
        ./startup.sh
    """
    shell(cmd)


def running_log(environ, start_response):
    params = environ['params']
    start_response('200 OK', [('Content-type', 'text/html')])
    yield STATIC_LOADER["app/log.html"].format(
        text=get_log(f"/data/tomcat7_finance_{params.get('tomcat')}/logs/catalina.out")).encode('utf-8')


def get_file_bytes(file):
    with open(file, "rb") as fp:
        return fp.read()


def get_config_text(file):
    with open(file, "r") as fp:
        return fp.read()


def write_config_text(file, text):
    with open(file, "w") as fp:
        fp.write(text)


def save(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    params = environ['params']
    port = params.get('tomcat')
    write_config_text(f"/data/tomcat7_finance_{port}/webapps/application.properties",
                      params.get("data"))
    cp(f"/data/tomcat7_finance_{port}")
    write_log(port, "修改并替换配置成功!")
    yield "ok".encode('utf-8')


def restart(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    params = environ['params']
    port = params.get("tomcat")
    passwd = params.get("pass")
    if passwd == 'a123456':
        try:
            tomcat = f"/data/tomcat7_finance_{port}"
            shutdown(port)
            time.sleep(1)
            start(tomcat)
            result = "重启成功"
        except Exception as e:
            logger.error(str(e))
            result = f"重启:{str(e)}"
    else:
        result = "重启操作密码错误！"
    write_log(port, result)
    yield result.encode('utf-8')


def edit(environ, start_response):
    params = environ['params']
    tomcat = params.get('tomcat')
    start_response('200 OK', [('Content-type', 'text/html')])
    yield STATIC_LOADER["app/edit.html"].replace("#config", get_config_text(
        f"/data/tomcat7_finance_{tomcat}/webapps/application.properties")).replace("#tomcat", tomcat).encode('utf-8')


def static(environ, start_response):
    path = environ['PATH_INFO'][1:]
    if path.find(".css") != -1:
        start_response('200 OK', [('Content-type', 'text/css')])
    elif path.find(".png") != -1:
        start_response('200 OK', [('Content-type', 'image/png')])
    else:
        start_response('200 OK', [('Content-type', 'text/html')])
    yield STATIC_LOADER[path]


def from_time_stamp(seconds=0):
    # remark: int(time.time()) 不能放到参数默认值，否则会初始化为常量
    if seconds == 0:
        seconds = int(time.time())
    return datetime.datetime.fromtimestamp(seconds, pytz.timezone('Asia/Shanghai')).strftime(
        '%m-%d %H:%M:%S')


def write_log(port, result):
    with open("file/log.txt", "a") as f:
        f.write(f"{from_time_stamp()}[{port}] {result}\n")


def log(_, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    yield get_log("file/log.txt", False, 15).encode("utf-8")


def get_package(_, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    yield package_name.encode("utf-8")


if __name__ == '__main__':
    from Resty import PathDispatcher
    from wsgiref.simple_server import make_server

    # Create the dispatcher and register functions
    dispatcher = PathDispatcher()
    dispatcher.register('GET', '/', hello)
    dispatcher.register('POST', '/upload', upload)
    dispatcher.register('GET', '/log-run', running_log)
    dispatcher.register('GET', '/edit', edit)
    dispatcher.register('POST', '/save', save)
    dispatcher.register('POST', '/restart', restart)
    dispatcher.register('GET', '/static/?', static)
    dispatcher.register('GET', '/log', log)
    dispatcher.register('GET', '/get-package', get_package)

    # Launch a basic server
    httpd = make_server('', 7777, dispatcher)
    logger.info('Serving on port 7777...')
    httpd.serve_forever()
