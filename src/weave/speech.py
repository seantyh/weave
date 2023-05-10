from dataclasses import dataclass, field
from typing import List, cast
from praatio import textgrid
from .utt_tg import Utterance
from .tg_writer import TextGridWriter
from .build_utts import (
      build_utts_words_chars,
      align_annots
    )

@dataclass
class Speech:
    utterances: List[Utterance] = field(default_factory=list)
    annot_fields: List[str] = field(default_factory=list)

    def __repr__(self):
        if self.annot_fields:
            supp = " ({})".format(", ".join(self.annot_fields))
        else:
            supp = ""

        out_str = ("<Speech: {} utterances, {:.2f} sec(s){}>"
          .format(len(self.utterances), 
                  self.utterances[-1].end-self.utterances[0].start,
                  supp))
        
        return out_str

    @classmethod 
    def from_utterances(cls, utterances: List[Utterance]):
        inst = cls()
        inst.utterances = utterances
        return inst
    
    @classmethod
    def from_dict(cls, d):
        if d["type"] != "Speech":
            raise TypeError("d['type'] is not a Speech")
        d["utterances"] = [Utterance.from_dict(x) for x in d["utterances"]]
        d.pop("type")
        return cls(**d)    

    def add_utterance(self, utt: Utterance):
        self.utterances.append(utt)

    @property
    def n_utterances(self):
        return len(self.utterances)
    
    @property
    def n_words(self):
        return sum(x.n_words() for x in self.utterances)
    
    def to_textgrid(
            self, 
            tg_path, 
            writer_cls=TextGridWriter
        ):
        
        writer_inst = writer_cls()
        writer_inst.export(self.utterances, tg_path)
    
    def to_dict(self):
        return {
            "utterances": [x.to_dict() for x in self.utterances],
            "annot_fields": self.annot_fields,
            "type": "Speech"
        }        
    
    @classmethod
    def from_textgrid_fon(cls, 
                          tg_path, 
                          annot_fields: List[str]=[]
            ) -> "Speech":
        tg = textgrid.openTextgrid(str(tg_path), False)

        tier_names = tg.tierNames
        if set(["utt", "ch", "word"])-set(tier_names):
            raise ValueError("TextGrid must have tiers named 'utt', 'ch', and 'word'")        
        
        annot_utt_tier = tg.getTier("utt")
        annot_chars_tier = tg.getTier("ch")
        annot_words_tier = tg.getTier("word")
        utts = build_utts_words_chars(
                annot_utt_tier, annot_words_tier, annot_chars_tier) # type: ignore
        speech = Speech.from_utterances(utts)

        # attach annotations

        for annot_field in annot_fields:
            if annot_field not in tg.tierNames:
                print("INFO: {} not found in TextGrid".format(annot_field))
                continue
            
            annot_tier = tg.getTier(annot_field)
            annot_tier = cast(textgrid.IntervalTier, annot_tier)
            speech.utterances = align_annots(
                  speech.utterances, annot_field, annot_tier)
            speech.annot_fields.append(annot_field)

        return speech
    