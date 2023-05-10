from dataclasses import dataclass, field
from typing import List, Optional
from textwrap import indent
from .tg_writer import TextGridWriter

indent1 = lambda x: indent(x, prefix=" ")

@dataclass
class TgInterval:
    start: float = 0
    end: float = 0
    label: str = ""    
    
    @classmethod
    def from_interval(cls, interval):
        return cls(interval.start,
                   interval.end, 
                   interval.label)    
        
    @classmethod
    def from_dict(cls, d):
        return cls(d["start"], 
                   d["end"], 
                   d["label"])
    
    def format_str(self):
        fstr = "[{:4.2f}-{:4.2f}] {}".format(
            self.start, 
            self.end,
            self.label
        )
        return fstr
    
    def _shift(self, t):
        self.start += t
        self.end += t

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "label": self.label
        }


@dataclass
class Phone(TgInterval):
    realization: str = ""
    note: str = ""
    
    def __hash__(self):
        return hash((self.start, self.end, self.label,
                     self.realization, self.note))

    def __repr__(self):
        if self.realization or self.note:            
            attrs = f"({self.note}/{self.realization})"
            out_str = f"<Phone: {self.format_str()} {attrs}>"
        else:
            out_str = f"<Phone: {self.format_str()}>"
        return out_str
    
    @classmethod
    def from_dict(cls, d):
        if d["type"] != "Phone":
            raise TypeError("d['type'] is not a Phone")        
        d.pop("type")
        return cls(**d)
    
    def validate(self):
        return True
    
    def shift(self, t):
        self._shift(t)

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "realization": self.realization,
            "note": self.note,
            "type": "Phone"
        })
        return base_dict
        

@dataclass
class Character(TgInterval):
    realization: str = ""
    note: str = ""    
    phones: List[Phone] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, d):
        if d["type"] != "Character":
            raise TypeError("d['type'] is not a Character")                    
        d["phones"] = [Phone.from_dict(x) for x in d["phones"]]
        d.pop("type")
        return cls(**d)
    
    def append_phone(self, phone):
        self.phones.append(phone)

    def __hash__(self):
        return hash((self.start, self.end, self.label,
                     self.realization, self.note))
    
    def __repr__(self):
        if self.realization or self.note:            
            attrs = f"({self.note}/{self.realization})"
            out_str = f"<Character: {self.format_str()} {attrs}>"
        else:
            out_str = f"<Character: {self.format_str()}>"
            
        if self.phones:
            out_str += "\n" + "\n".join(
                indent1(str(x)) for x in self.phones
            )
        return out_str        
    
    def iter_phones(self):
        for phone_x in self.phones:
            yield phone_x
            
    def validate(self):
        if not self.phones: return True
        if self.start != self.phones[0].start or \
           self.end != self.phones[-1].end:
            print(f"Validation failed: {self}")
        _ = [x.validate() for x in self.phones]
        return True
    
    def shift(self, t):
        self._shift(t)
        _ = [x.shift(t) for x in self.phones]            

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "realization": self.realization,
            "note": self.note,
            "phones": [x.to_dict() for x in self.phones],
            "type": "Character"
        })
        return base_dict
        
@dataclass
class Word(TgInterval):
    characters: List[Character] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d):
        if d["type"] != "Word":
            raise TypeError("d['type'] is not a Word")        
        d["characters"] = [Character.from_dict(x) for x in d["characters"]]
        d.pop("type")

        return cls(**d)
    
    def append_character(self, charac):
        self.characters.append(charac)

    def __hash__(self):
        return hash((self.start, self.end, self.label,
                     tuple(self.characters)))
     
    def __repr__(self):
        out_str = f"<Word: {self.format_str()}>\n"
        out_str += "\n".join(
            indent1(str(x)) for x in self.characters
        )
        return out_str
    
    def iter_characters(self):
        yield from self.characters        
        
    def iter_phones(self):
        for char_x in self.characters:
            yield from char_x.iter_phones()
    
    def validate(self):
        if not self.characters: return True
        if self.start != self.characters[0].start or \
           self.end != self.characters[-1].end:
            print(f"Validation failed: {self}")
        _ = [x.validate() for x in self.characters]
        return True
    
    def shift(self, t):
        self._shift(t)
        _ = [x.shift(t) for x in self.characters]     
    
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "characters": [x.to_dict() for x in self.characters],
            "type": "Word"
        })
        return base_dict
@dataclass
class Utterance(TgInterval):
    words: List[Word] = field(default_factory=list)
        
    @classmethod
    def from_words(cls, words: List[Word]):
        inst = cls(words[0].start, 
                   words[-1].end, 
                   " ".join(x.label for x in words))
        inst.words = words
        return inst

    @classmethod
    def from_dict(cls, d):
        if d["type"] != "Utterance":
            raise TypeError("d['type'] is not an Utterance")        
        d["words"] = [Word.from_dict(x) for x in d["words"]]
        d.pop("type")
        
        return cls(**d)
        
    def __hash__(self):
        return hash((self.start, self.end, self.label,
                     tuple(self.words)))
    
    def __repr__(self):
        out_str = f"<Utterance: {self.format_str()}>\n"
        out_str += "\n".join(
            indent1(str(x)) for x in self.words
        )
        return out_str
        
    def n_words(self):
        return len(self.words)
    
    def iter_characters(self):
        for word_x in self.words:
            yield from word_x.iter_characters()
            
    def iter_phones(self):
        for word_x in self.words:
            yield from word_x.iter_phones()
    
    def append_word(self, word):
        self.words.append(word)
        
    def validate(self):
        if not self.words: return True
        if self.start != self.words[0].start or \
           self.end != self.words[-1].end:
            print(f"Validation failed: {self}")
        _ = [x.validate() for x in self.words]
        return True
    
    def shift(self, t):
        self._shift(t)
        _ = [x.shift(t) for x in self.words]  

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "words": [x.to_dict() for x in self.words],
            "type": "Utterance"
        })
        return base_dict
