#coding=utf-8
#condition
import threading  
import random  
import time  

condition = threading.Condition()
product = 0
class Producer(threading.Thread):
    goods = [1, 2, 3]

    def __init__(self, threadName):
        threading.Thread.__init__(self,name=threadName)  
        
    def run(self):
        global condition, product
        while True:
            if condition.acquire():
                if product == 0:
                    product = random.randrange(1, 4)
                    if product == 1:
                        print 'Produce Tape, Battery'
                    elif product == 2:
                        print 'Produce Walkman, Battery'
                    else:
                        print 'Produce Walkman, Tape'
                    condition.notifyAll()
                else:
                    condition.wait()
                condition.release()
                
class Listener(threading.Thread):
    
    def __init__(self, threadName, need):
        threading.Thread.__init__(self,name=threadName)  
        self.need = need
               
    def run(self):
        global condition, product
        while True:
            if condition.acquire():
                if product == self.need:
                    if self.need == 1:
                        print self.getName()+': Buy Tape, Battery. Listening'
                    elif self.need == 2:
                        print self.getName()+': Buy Walkman, Battery. Listening'
                    else:
                        print self.getName()+': Buy Walkman, Tape. Listening'
                    product = 0
                    time.sleep(2)
                    condition.notifyAll()
                else:
                    condition.wait()
                condition.release()

threads=[]
semaphore0 = threading.Semaphore(1)
semaphore1 = threading.Semaphore(0)
semaphore2 = threading.Semaphore(0)
semaphore3 = threading.Semaphore(0)

threads.append(Producer("Producer"))
threads.append(Listener("Listener1", 1))
threads.append(Listener("Listener2", 2))
threads.append(Listener("Listener3", 3))

for thread in threads: 
   thread.start() 
