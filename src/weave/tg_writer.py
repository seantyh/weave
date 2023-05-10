#type: ignore
from itertools import chain
from typing import List
from praatio import textgrid

class TextGridWriter:
    def __init__(self):
        pass
    
    def export(self, utts:List["Utterance"], fpath):
        tg = textgrid.Textgrid()
        minT = utts[0].start
        maxT = utts[-1].end        
        
        utt_entries = [
            (utt_x.start, utt_x.end, utt_x.label)
            for utt_x in utts
        ]
        
        word_entries = [
            (word_x.start, word_x.end, word_x.label)
            for word_x 
            in chain.from_iterable(
                utt_x.words for utt_x in utts)
        ]
        
        charac_entries = [
            (char_x.start, char_x.end, char_x.label)
            for char_x 
            in chain.from_iterable(
                utt_x.iter_characters() for utt_x in utts)
        ]
        
        phone_entries = [
            (phone_x.start, phone_x.end, phone_x.label)
            for phone_x 
            in chain.from_iterable(
                utt_x.iter_phones() for utt_x in utts)
        ]
        
        note_entries = [
            (phone_x.start, phone_x.end, phone_x.note)
            for phone_x 
            in chain.from_iterable(
                utt_x.iter_phones() for utt_x in utts)
            if phone_x.note
        ]
        
        rz_entries = [
            (phone_x.start, phone_x.end, phone_x.realization)
            for phone_x 
            in chain.from_iterable(
                utt_x.iter_phones() for utt_x in utts)
            if phone_x.realization
        ]

        utt_tier = textgrid.IntervalTier('utterances', utt_entries, minT, maxT)
        word_tier = textgrid.IntervalTier('words', word_entries, minT, maxT)
        charac_tier = textgrid.IntervalTier('characters', charac_entries, minT, maxT)
        phone_tier = textgrid.IntervalTier('phones', phone_entries, minT, maxT)
        note_tier = textgrid.IntervalTier('notes', note_entries, minT, maxT)
        rz_tier = textgrid.IntervalTier('realizations', rz_entries, minT, maxT)
        
        for tier in (utt_tier, word_tier,
                     charac_tier, phone_tier,
                     note_tier, rz_tier):
            tg.addTier(tier)
        
        tg.save(fpath, 
                format="short_textgrid",
                includeBlankSpaces=True)