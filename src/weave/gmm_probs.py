import re
import subprocess
from io import BytesIO
from pathlib import Path
from typing import cast, Tuple
import numpy as np
from kaldiio.matio import read_token, read_kaldi
from icecream import ic

def compute_gmmlik(
      utt_id: str, 
      ali_dir: Path, 
      corpus_dir: Path
    ) -> np.ndarray:
  trfeats, split_id = call_transform_feature(utt_id, ali_dir, corpus_dir)
  tok, gmmlik = call_gmmlik(trfeats, split_id, ali_dir)
  gmmlik = cast(np.ndarray, gmmlik)
  assert tok == utt_id, "utt_id does not match"
  return gmmlik

def call_transform_feature(utt_id, ali_dir, corpus_dir):
  
  feat_scp = find_utt_feat_scp(utt_id, corpus_dir)
  assert feat_scp, "utt_id not found in feat.*.scp"

  feat_path = Path("./tmp/trfeats.scp")
  feat_path.parent.mkdir(parents=True, exist_ok=True)
  feat_path.write_text(f"{utt_id} {feat_scp}\n")
  split_id = re.findall(r"\.(\d)\.", str(feat_scp))

  assert split_id, "split_id is not found in feat.*.scp"
  split_id = split_id[0]

  cmd = subprocess.Popen([
      "splice-feats",
      "--left-context=3", "--right-context=3",
      "scp,s,cs:" + str(feat_path), "ark:-"],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)
  cmd2 = subprocess.Popen([
      "transform-feats",
      str(ali_dir / "lda.mat"),
      "ark:-", "ark:-"],
      stdin=cmd.stdout,
      stdout=subprocess.PIPE,
  )
  tr_feats = cmd2.stdout.read() # type:ignore

  # clean up
  feat_path.unlink()

  return tr_feats, split_id

def call_gmmlik(tr_feats: bytes, split_id: str, ali_dir: Path):
  cmd = subprocess.Popen([
      "gmm-compute-likes",
      str(ali_dir / f"boost.1.{split_id}.mdl"),
      "ark:-", "ark:-"],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
  )
  gmm_probs, _ = cmd.communicate(tr_feats) # type:ignore
  gmm_probs_f = BytesIO(gmm_probs)
  token = read_token(gmm_probs_f)
  mat = read_kaldi(gmm_probs_f) # type:ignore
  assert token is not None

  return token, mat

def find_utt_feat_scp(utt_id, corpus_dir):
  feat_scps = (corpus_dir / "split3").glob("feats.*.scp")
  feat_path = None
  for feat_scp_path in feat_scps:
    lines = feat_scp_path.read_text().split("\n")
    for ln in lines:
      fields = ln.split()
      if len(fields) < 2: continue
      utt_id_x = fields[0]
      if utt_id == utt_id_x:
        feat_path = Path(fields[1])
        return feat_path