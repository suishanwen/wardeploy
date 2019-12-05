import os
from file_read_backwards import FileReadBackwards
from Logger import logger

locker = {
    "9093": False,
    "9193": False,
    "9293": False,
    "9393": False
}


def get_log(file):
    with FileReadBackwards(file, encoding="utf-8") as frb:
        lines = []
        while len(lines) < 1000:
            line = frb.readline()
            if not line:
                break
            lines.append(line)
    return "<br/>".join(lines)


def hello(_, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    with open('app/index.html', 'r', encoding="utf-8") as fp:
        yield fp.read().encode('utf-8')


def upload(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    params = environ['params']
    port = params.get('tomcat')
    if locker[port]:
        yield f"{port}当前正在处理锁定中,请稍后再试".encode('utf-8')
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
        except Exception as e:
            logger.error(str(e))
        finally:
            locker[port] = False
    yield "成功".encode('utf-8')


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


def mv(tomcat, port):
    cmd = f"mv /data/wardeploy/file/{port}/mvcost {tomcat}/webapps/finance"
    shell(cmd)


def cp(tomcat):
    cmd0 = f"rm -rf {tomcat}/webapps/WEB-INF/application.properties"
    cmd = f"cp {tomcat}/webapps/application.properties {tomcat}/webapps/finance/WEB-INF/application.properties"
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
    with open('app/log.html', 'r', encoding="utf-8") as fp:
        yield fp.read().format(text=get_log(f"/data/tomcat7_finance_{params.get('tomcat')}/logs/catalina.out")).encode(
            'utf-8')


def get_config_text(file):
    with open(file, "r") as fp:
        return fp.read()


def write_config_text(file, text):
    with open(file, "w") as fp:
        fp.write(text)


def save(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    params = environ['params']
    write_config_text(f"/data/tomcat7_finance_{params.get('tomcat')}/finance/webapps/application.propertied",
                      params.get("data"))
    yield "ok".encode('utf-8')


def edit(environ, start_response):
    params = environ['params']
    tomcat = params.get('tomcat')
    start_response('200 OK', [('Content-type', 'text/html')])
    with open('app/edit.html', 'r', encoding="utf-8") as fp:
        yield fp.read().replace("#config", get_config_text(
            f"/data/tomcat7_finance_{tomcat}/finance/webapps/application.propertied")) \
            .replace("#tomcat", tomcat).encode('utf-8')


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
    # Launch a basic server
    httpd = make_server('', 7777, dispatcher)
    logger.info('Serving on port 7777...')
    httpd.serve_forever()
