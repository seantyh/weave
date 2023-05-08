from pathlib import Path
from .am_struct import TransitionModel
from .read_utils import read_table

class MfaAgent:
    def __init__(self, base_dir, corpus_name):
      mfa_dir = Path(base_dir)
      self.ali_dir = mfa_dir / "alignment"
      self.dic_dir = mfa_dir / "dictionary"
      self.data_dir = mfa_dir / corpus_name
      self.phones = self.load_phones()
      self.words = self.load_words()
      self.tmodel = self.load_transition_model()
    
    def load_phones(self):
      phones_txt = (self.dic_dir/"phones/phones.txt").read_text()
      return read_table(phones_txt)

    
    def load_words(self):
      words_path = list(self.dic_dir.glob("*/words.txt"))[0]
      words_txt = words_path.read_text()
      return read_table(words_txt)
    
    def load_transition_model(self):
      mdl = (self.ali_dir/"final.mdl.txt").read_text()
      return TransitionModel.from_text(mdl)

