import datetime

class APRSMessage:
    def __init__(self,source,dest,content,ident):
        self.source = source
        self.dest = dest
        self.content = content
        self.ident = ident
        self.timestamp = datetime.datetime.now()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and\
                self.source == other.source and\
                self.dest == other.dest and\
                self.content == other.content and\
                self.ident == other.ident

    def __hash__(self):
       return hash(self.source) ^ hash(self.dest) ^\
               hash(self.content) ^ hash(self.ident)
