#
# Copyright (c) 2021 FunnelBeam
#


class ServerAdapter(object):
    quiet = False

    def __init__(self, host='127.0.0.1', port=8080, **options):
        self.options = options
        self.host = host
        self.port = int(port)

    def run(self, handler):  # pragma: no cover
        pass

    def __repr__(self):
        args = ', '.join('%s=%s' % (k, repr(v))
                          for k, v in self.options.items())
        return "%s(%s)" % (self.__class__.__name__, args)


class GunicornServer(ServerAdapter):
    """ Untested. See http://gunicorn.org/configure.html for options. """

    def run(self, handler):
        from gunicorn.app.base import BaseApplication

        if self.host.startswith("unix:"):
            config = {'bind': self.host}
        else:
            config = {'bind': "%s:%d" % (self.host, self.port)}

        config.update(self.options)

        class GunicornApplication(BaseApplication):
            def load_config(self):
                for key, value in config.items():
                    self.cfg.set(key, value)

            def load(self):
                return handler

        GunicornApplication().run()


SERVERS = {
    'gunicorn': GunicornServer
}


def run(app=None, server='gunicorn', host='127.0.0.1', port=8080, **kwargs):

    try:
        server = SERVERS.get(server)
        if isinstance(server, type):
            server = server(host=host, port=port, **kwargs)

        if not isinstance(server, ServerAdapter):
            raise ValueError("Unknown or unsupported server: %r" % server)

        server.run(app)
    except KeyboardInterrupt:
        pass
    except (SystemExit, MemoryError):
        raise
