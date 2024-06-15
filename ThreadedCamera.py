from threading import Thread
import cv2, time

class ThreadedCamera(object):
    def __init__(self, src=""):
        self.capture = cv2.VideoCapture(src)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
       
        # FPS = 1/X
        # X = desired FPS
        self.FPS = 1/30
        self.FPS_MS = int(self.FPS * 1000)
        self.should_work = True        
        # Start frame retrieval thread
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.should_work = False
    def update(self):
        while self.should_work:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
            time.sleep(self.FPS)
            
    def show_frame(self):
        cv2.imshow('frame', self.frame)
        cv2.waitKey(self.FPS_MS)

