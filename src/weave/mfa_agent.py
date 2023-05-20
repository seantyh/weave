from pathlib import Path
import subprocess
from .am_struct import TransitionModel
from .read_utils import read_table, read_wave_scp
from .gmm_probs import compute_gmmlik
class MfaAgent:
    def __init__(self, base_dir, corpus_name):
      mfa_dir = Path(base_dir)
      self.ali_dir = mfa_dir / "alignment"
      self.dic_dir = mfa_dir / "dictionary"
      self.data_dir = mfa_dir / corpus_name
      self.phones = self.load_phones()
      self.words = self.load_words()
      self.wav2uttid = read_wave_scp(self.data_dir)
      self.tmodel = self.load_transition_model()
    
    def load_phones(self):
      phones_txt = (self.dic_dir/"phones/phones.txt").read_text()
      return read_table(phones_txt)

    
    def load_words(self):
      words_path = list(self.dic_dir.glob("*/words.txt"))[0]
      words_txt = words_path.read_text()
      return read_table(words_txt)
    
    def load_transition_model(self):
      mdl_path = self.ali_dir / "final.mdl"
      cvt_cmd = subprocess.Popen([
                "gmm-copy", 
                "--binary=false", 
                str(mdl_path), "-"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE)
      mdl = cvt_cmd.stdout.read().decode("utf-8")  # type:ignore
      err = cvt_cmd.stderr.read().decode("utf-8")  # type:ignore
      print("STDERR:", err)
      return TransitionModel.from_text(mdl)
    
    def compute_gmm(self, utt_id):
      return compute_gmmlik(utt_id, self.ali_dir, self.data_dir)

