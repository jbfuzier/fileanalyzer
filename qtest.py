from multiprocessing import Queue, Process

def proc(q):
    print q.__dict__
    c = q.get()
    print "Proc 1 : %s"%c

a=Queue()
print a.__dict__
p=Process(target=proc, args=(a,))
p.start()
a.put("test")
pass