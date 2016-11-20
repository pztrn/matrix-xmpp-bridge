import threading

class Queue:
    def __init__(self):
        self.__queue = []
        self.__lock = threading.Lock()

    def add_message(self, message):
        self.__lock.acquire(blocking = True)
        self.__queue.append(message)
        self.__lock.release()

    def get_message(self):
        self.__lock.acquire(blocking = True)
        msg = self.__queue.pop(0)
        self.__lock.release()
        return msg

    def is_empty(self):
        return len(self.__queue) == 0

    def items_in_queue(self):
        return len(self.__queue)
