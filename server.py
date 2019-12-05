import subprocess
from file_read_backwards import FileReadBackwards
from Logger import logger


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
    with open('app/hello.html', 'r', encoding="utf-8") as fp:
        yield fp.read().encode('utf-8')


def upload(environ, start_response):
    params = environ['params']
    port = params.get('tomcat')
    tomcat = f"/data/tomcat7_finance_{port}"
    name = params.get("name")
    file_name = f"{name.split('.')[0]}-{port}.zip"
    file = params.get("file")
    with open(f"file/{file_name}", 'wb') as f:
        f.write(file)
    shutdown(port)
    unzip(file_name)
    rm(tomcat)
    mv(tomcat, file_name)
    cp(tomcat)
    start(tomcat)
    start_response('200 OK', [('Content-type', 'text/html')])
    yield "ok".encode('utf-8')


def shell(cmd):
    logger.info(cmd)
    _sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    _sp.wait()


def unzip(file_name):
    cmd = f"cd /data/wardeploy/file" \
          f"unzip /data/wardeploy/file/{file_name}"
    shell(cmd)


def rm(tomcat):
    cmd = f"rm -rf {tomcat}/webapps/finance"
    shell(cmd)


def mv(tomcat, file_name):
    cmd = f"mv /data/wardeploy/file/{file_name.split('.')[0]} {tomcat}/webapps"
    shell(cmd)


def cp(tomcat):
    cmd0 = f"rm -rf {tomcat}/webapps/WEB-INF/application.properties"
    cmd = f"cp {tomcat}/webapps/application.properties {tomcat}/webapps/WEB-INF/application.properties"
    shell(cmd0)
    shell(cmd)


def shutdown(port):
    cmd = "ps -ef | grep tomcat7_finance_" + port + " | grep -v grep | awk '{print $2}' | xargs kill -9"
    shell(cmd)


def start(tomcat):
    cmd = f"cd {tomcat}/bin" \
          f"./startup.sh"
    shell(cmd)


if __name__ == '__main__':
    from Resty import PathDispatcher
    from wsgiref.simple_server import make_server

    # Create the dispatcher and register functions
    dispatcher = PathDispatcher()
    dispatcher.register('GET', '/', hello)
    dispatcher.register('POST', '/upload', upload)

    # Launch a basic server
    httpd = make_server('', 7777, dispatcher)
    logger.info('Serving on port 7777...')
    httpd.serve_forever()
