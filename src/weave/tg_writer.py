from typing import List
from .utt_tg import Utterance
from praatio import textgrid

class TextGridWriter:
    def __init__(self):
        pass
    
    def write(self, utts:List[Utterance], fpath):
        tg = textgrid.TextGrid()
        minT = utts[0].start
        maxT = utts[-1].end
        utt_tier = textgrid.IntervalTier('utterances', [], minT, maxT)
        word_tier = textgrid.IntervalTier('words', [], minT, maxT)
        charac_tier = textgrid.IntervalTier('characters', [], minT, maxT)
        phone_tier = textgrid.IntervalTier('phones', [], minT, maxT)
        note_tier = textgrid.IntervalTier('notes', [], minT, maxT)
        rz_tier = textgrid.IntervalTier('realizations', [], minT, maxT)
        
        utt_tier.entries = [
            (utt_x.start, utt_x.end, utt_x.label)
            for utt_x in utts
        ]
        
        word_tier.entries = [
            (word_x.start, word_x.end, word_x.label)
            for word_x 
            in chain.from_iterable(
                utt_x.words for utt_x in utts)
        ]
        
        charac_tier.entries = [
            (char_x.start, char_x.end, char_x.label)
            for char_x 
            in chain.from_iterable(
                utt_x.iter_characters() for utt_x in utts)
        ]
        
        phone_tier.entries = [
            (phone_x.start, phone_x.end, phone_x.label)
            for phone_x 
            in chain.from_iterable(
                utt_x.iter_phones() for utt_x in utts)
        ]
        
        note_tier.entries = [
            (phone_x.start, phone_x.end, phone_x.note)
            for phone_x 
            in chain.from_iterable(
                utt_x.iter_phones() for utt_x in utts)
            if phone_x.note
        ]
        
        rz_tier.entries = [
            (phone_x.start, phone_x.end, phone_x.realization)
            for phone_x 
            in chain.from_iterable(
                utt_x.iter_phones() for utt_x in utts)
            if phone_x.realization
        ]
        
        for tier in (utt_tier, word_tier
                     charac_tier, phone_tier,
                     note_tier, rz_tier):
            tg.addTier(tier)
        
        tg.save(fpath, 
                format="short_textgrid",
                includeBlankSpaces=True)