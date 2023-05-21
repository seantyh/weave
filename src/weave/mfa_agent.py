import re
import json
import subprocess
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from .am_struct import TransitionModel
from .read_utils import read_table, read_wave_scp
from .gmm_probs import compute_gmmlik
from .data_types import PhoneGranularity
from .speech import Speech

PHONE_TABLE = """
sil spn 
a aj aw 
o ow
ə ɥ 
e ej  
i io
j w u y
p pʰ m f
t tʰ n l
k kʰ x 
tɕ tɕʰ  
ʈʂ ʈʂʰ ʂ ʐ ʐ̩
ts tsʰ ɕ
z z̩ s 
ŋ ŋ̍ ɻ ʔ
"""

class MfaAgent:
    def __init__(
          self,
          base_dir,
          corpus_name,
          granularity=PhoneGranularity.NOTONE,
          speech_json_dir=None
          ):
      mfa_dir = Path(base_dir)
      self.ali_dir = mfa_dir / "alignment"
      self.dic_dir = mfa_dir / "dictionary"
      self.data_dir = mfa_dir / corpus_name
      self.phones = self._load_phones()
      self.words = self._load_words()
      self.wav2uttid = read_wave_scp(self.data_dir)
      self.tmodel = self._load_transition_model()
      self.phone2pdfid = self._build_phone2pdfid(granularity)
      self.phone_table = [x for x in 
                          PHONE_TABLE.strip().replace("\n", " ").split(" ")
                          if x]
      if speech_json_dir:
        self.speeches = self._load_speeches(speech_json_dir)
      else:
        self.speech_json_dir = None
    
    def _load_phones(self):
      phones_txt = (self.dic_dir/"phones/phones.txt").read_text()
      return read_table(phones_txt)

    
    def _load_words(self):
      words_path = list(self.dic_dir.glob("*/words.txt"))[0]
      words_txt = words_path.read_text()
      return read_table(words_txt)
    
    def _load_transition_model(self):
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
    
    def _load_speeches(self, speech_json_dir):
        speech_json_dir = Path(speech_json_dir)
        speeches = []
        for json_path in speech_json_dir.glob("*.mfa.json"):
            json_data = json.loads(json_path.read_text())
            speech_x = Speech.from_dict(json_data)
            speech_x.build_parent()
            speeches.append(speech_x)
        return speeches

    def _build_phone2pdfid(
        self, 
        granularity=PhoneGranularity.NOTONE):

      def extract_phone_type(x, granularity):
          """Strip tones and states for each phone token
          """
          x = x.split("_")[0]
          if granularity == PhoneGranularity.NOTONE:
            x = re.sub("[\u02e5-\u02e9]+", "", x)
          return x
          
      tm = self.tmodel

      pid2phone = [0]*len(self.phones)
      for phone_x, pid_x in self.phones.items():
          pid2phone[pid_x] = phone_x

      phone2pdfid = {}
      pdfid2phone = {}  # not used for now, but the mapping is generated in Kaldi
                        # might be useful in the future
      for triple_x in tm.triples:
          phone_id, hmm_state, pdf_id = triple_x
          phone = extract_phone_type(pid2phone[phone_id], granularity)
          phone2pdfid.setdefault(phone, []).append(pdf_id)
          pdfid2phone.setdefault(pdf_id, []).append(phone)

      return phone2pdfid
    
    def get_phoneid(self, phone):
       return self.phone_table.index(phone)

    def compute_gmm(self, utt_id):
      gmmlik = compute_gmmlik(utt_id, self.ali_dir, self.data_dir)
      phone2pdfid = self.phone2pdfid
      gmmprob = np.zeros((gmmlik.shape[0], len(self.phone_table)))
      for phone_idx, phone_x in enumerate(self.phone_table):
        pdfids_x = phone2pdfid.get(phone_x, [])
        if not pdfids_x:
           assert False, phone_x
        # fill in the logits first
        gmmprob[:, phone_idx] = logsumexp(gmmlik[:, pdfids_x], axis=1)
      lgmmprob = gmmprob - logsumexp(gmmprob, axis=1, keepdims=True)

      return lgmmprob

