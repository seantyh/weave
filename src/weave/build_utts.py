from typing import List, Dict
from itertools import chain
from praatio.textgrid import IntervalTier
from .utt_tg import *
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def build_utts_words_chars(
        utier: IntervalTier, 
        wtier: IntervalTier, 
        ctier: IntervalTier
    ) -> List[Utterance]:
    
    utt_idx = 0
    word_idx = 0
    
    cur_utt = Utterance.from_interval(utier.entries[0])    
    cur_word = Word.from_interval(wtier.entries[0])
    utts = []
        
    for char_idx, char_x in enumerate(ctier.entries):
        if (char_x.start >= cur_word.end):  #type: ignore
            word_idx += 1
            cur_utt.append_word(cur_word)
            cur_word = Word.from_interval(wtier.entries[word_idx])
            
        if (char_x.start >= cur_utt.end):  #type: ignore
            utt_idx += 1
            utts.append(cur_utt)
            cur_utt = Utterance.from_interval(utier.entries[utt_idx]) 
                    
        cur_word.append_character(
            Character.from_interval(char_x))
    
    cur_utt.append_word(cur_word)
    utts.append(cur_utt)
    
    return utts


def align_annots(
        utt_list: List[Utterance],
        tier_name: str,
        annot_tier: IntervalTier):        

    annot_idx = 0
    cur_annot = annot_tier.entries[annot_idx]
    char_iter = chain.from_iterable(
                (x.iter_characters() for x in utt_list))
    
    for char_x in char_iter:

        mid_t = (cur_annot.start + cur_annot.end)/2   #type: ignore
        cstart = char_x.start
        cend = char_x.end
        if cstart <= mid_t <= cend:
            setattr(char_x, tier_name, cur_annot.label)            
            annot_idx += 1            
            # print(char_x, cur_annot.label)

        if annot_idx >= len(annot_tier.entries):            
            break
        cur_annot = annot_tier.entries[annot_idx]
            
    return utt_list

def build_words_phones(
        wtier: IntervalTier, 
        ptier: IntervalTier
    ) -> List[Word]:
    
    word_idx = 0
    words = []
    
    cur_word = Word.from_interval(wtier.entries[0])
    char_entries = []
    for phone_idx, phone_x in enumerate(ptier.entries):    
        if (phone_x.start >= cur_word.end):  #type: ignore
            word_idx += 1
            words.append(cur_word)
            cur_word = Word.from_interval(wtier.entries[word_idx])                    
        cur_word.append_character(
            Character.from_interval(phone_x)
        )
    words.append(cur_word)        
    return words

def build_characters(
        words: List[Word],
        syll_map: Dict[str, Dict[str, str]]
    ) -> List[Word]:
    
    new_wlist = []
    for word_x in words:
        phones = [Phone(x.start, x.end, x.label) for x in word_x.characters]
        
        word_copy = Word(word_x.start, word_x.end, word_x.label)
        ipa = " ".join(x.label for x in phones)
        sylls = syll_map.get(ipa, {}).get("syllables")
        if not sylls:            
            char_x = Character(phones[0].start, phones[-1].end, "<UNK>")
            char_x.phones = phones
            word_copy.append_character(char_x)
        else:
            phone_idx = 0
            syll_list = sylls.split("|")            
            for syll_i, syll_x in enumerate(syll_list):
                pholist = syll_x.strip().split()
                # declare a container, set the start and end later
                cur_char = Character(word_x.start, word_x.end, word_x.label[syll_i])                
                for pho_x in pholist:
                    cur_phone = phones[phone_idx]
                    cur_char.append_phone(cur_phone)
                    phone_idx += 1
                cur_char.start = cur_char.phones[0].start
                cur_char.end = cur_char.phones[-1].end                
                word_copy.append_character(cur_char)
                
        new_wlist.append(word_copy)
    return new_wlist

def align_with_utterance_cyy_annot(
        mfa_utt: Utterance, 
        ref_utt: Utterance
    ) -> Utterance:
    """
    Align mfa_utt with ref_utt by their words. The annotations of character-level in the ref_utt 
    will be copied to the annotations of the phone-level in mfa_utt.
    This function assumes the ref_utt is built from CYY annotation.
    """

    shift_t = ref_utt.start - mfa_utt.start
    mfa_utt.shift(shift_t)
    mfa_words = mfa_utt.words
    annot_words = ref_utt.words
    for mfa_word_x, annot_word_x in zip(mfa_words, annot_words):
        if mfa_word_x.label.lower() != annot_word_x.label.lower():
            logger.warn("The labels are not matching, skipped: {}, {}"
                    .format(mfa_word_x.label, annot_word_x.label))
            continue

        mfa_chars = mfa_word_x.characters
        annot_chars = annot_word_x.characters
        if len(mfa_chars) == len(annot_chars):
            for mfa_char_x, annot_char_x in zip(mfa_chars, annot_chars):
                if annot_char_x.realization:
                    mfa_char_x.phones[0].realization = annot_char_x.realization
                if annot_char_x.note:
                    mfa_char_x.phones[0].note = annot_char_x.note
        else:

            annot_notes = [x.note for x in annot_chars if x.note]
            annot_rzs = [x.realization for x in annot_chars if x.realization]

            if len(annot_notes) == len(annot_rzs) == 0:
                # Although the characters do not match, there is no annotations in the data
                # we can safely skip this word.
                continue

            logger.info("Characters are not matching: {} (MFA), {} (Annot)".format(
                "".join(x.label for x in mfa_chars),
                "".join(x.label for x in annot_chars)
            ))

            if len(annot_notes)==1:
                logger.info("One note is aligned to the first MFA phone.")
                mfa_chars[0].phones[0].note = annot_notes[0]
            elif len(annot_notes) > 1:
                mfa_chars[0].phones[0].note = f"({'/'.join(annot_notes)})"
                logger.info("More than one notes are merged in to the first MFA phone.")

            if len(annot_rzs)==1:
                logger.info("One rz note is aligned to the first MFA phone.")
                mfa_chars[0].phones[0].realization = annot_rzs[0]
            elif len(annot_rzs) > 1:
                logger.info("More than one rz notes are merged in to the first MFA phone")
                mfa_chars[0].phones[0].realization = f"({'/'.join(annot_rzs)})"
            
    mfa_utt.validate()
    return mfa_utt