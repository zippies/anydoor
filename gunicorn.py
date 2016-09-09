import os
bind = "0.0.0.0:2016"
workers = os.cpu_count()*2 + 1
worker_class = "sync"
backlog = 2048
reload = True
debug = True
timeout = 120
