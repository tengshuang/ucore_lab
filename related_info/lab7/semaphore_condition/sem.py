#coding=utf-8
#semaphore
import threading  
import random  
import time  

class Producer(threading.Thread):
    goods = [1, 2, 3]

    def __init__(self, threadName, semaphore0, semaphore1, semaphore2, semaphore3):
        threading.Thread.__init__(self,name=threadName)  
        self.semaphore0 = semaphore0
        self.semaphore1 = semaphore1
        self.semaphore2 = semaphore2
        self.semaphore3 = semaphore3

    def run(self):
        while True:
            self.semaphore0.acquire()
            good = random.randrange(1, 4)
            if good == 1:
                print 'Produce Tape, Battery'
                self.semaphore1.release()
            elif good == 2:
                print 'Produce Walkman, Battery'
                self.semaphore2.release()
            else:
                print 'Produce Walkman, Tape'
                self.semaphore3.release()

class Listener(threading.Thread):
    
    def __init__(self, threadName, need, semaphore0, semaphore):
        threading.Thread.__init__(self,name=threadName)  
        self.need = need
        self.semaphore0 = semaphore0
        self.semaphore = semaphore
        
    def run(self):
        while True:
            self.semaphore.acquire()
            if self.need == 1:
                print self.getName()+': Buy Tape, Battery. Listening'
            elif self.need == 2:
                print self.getName()+': Buy Walkman, Battery. Listening'
            else:
                print self.getName()+': Buy Walkman, Tape. Listening'
            time.sleep(2)
            self.semaphore0.release()
            

threads=[]
semaphore0 = threading.Semaphore(1)
semaphore1 = threading.Semaphore(0)
semaphore2 = threading.Semaphore(0)
semaphore3 = threading.Semaphore(0)

threads.append(Producer("Producer", semaphore0, semaphore1, semaphore2, semaphore3))
threads.append(Listener("Listener1", 1, semaphore0, semaphore1))
threads.append(Listener("Listener2", 2, semaphore0, semaphore2))
threads.append(Listener("Listener3", 3, semaphore0, semaphore3))

for thread in threads: 
   thread.start() 
