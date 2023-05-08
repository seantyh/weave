from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import numpy as np
from .read_utils import find_tags, consume_tag, consume_integer

@dataclass
class HmmState:
  state_idx: int
  pdf_class: Optional[int]
  transitions: List[Tuple[int, float]]

  def __repr__(self):
    return (f"HmmState(state_idx={self.state_idx},pdf_class={self.pdf_class}"
            f"  transitions={self.transitions}") 
  
  @classmethod
  def from_text(cls, text):
    state_idx, state_x = consume_integer(text)
    pdf_class, state_x = consume_tag("PdfClass", state_x)
    transitions = []
    while True:
      transition, state_x = consume_tag("Transition", state_x)
      transition = transition.strip()
      if transition == "":
        break
      else:
        transition = transition.split()
        trans = (int(transition[0]), float(transition[1]))
        transitions.append(trans)
    
    assert state_idx is not None
    pdf_class = int(pdf_class) if pdf_class else None
    return cls(int(state_idx), pdf_class, transitions)

@dataclass
class TopologyEntry:
  phone_ids: List[int]
  hmm_states: List[HmmState]

  def __repr__(self):
    phone_ids_repr = ', '.join(str(x) for x in self.phone_ids[:10])
    if len(self.phone_ids) > 10:
      phone_ids_repr += "..."

    return ("TopologyEntry(\n"
      f"  phone_ids={phone_ids_repr},\n"
      "  hmm_states=\n    " + 
      '\n    '.join(str(x) for x in self.hmm_states) +
    ")")

  @classmethod
  def from_text(cls, text):
    phone_contents = find_tags("ForPhones", text)[0]
    state_content = find_tags("State", text)
    phone_ids = [int(x) for x in phone_contents.strip().split()]            
    hmm_states = [HmmState.from_text(x) for x in state_content]
    return cls(phone_ids, hmm_states)

@dataclass
class HmmTopology:
  entries: List[TopologyEntry]
  phone_topo: Dict[int, TopologyEntry]

  def __repr__(self):
    return f"HmmTopology({len(self.entries)} TopoEntries)"
  
  @classmethod
  def from_text(cls, text):
    topo_entries = find_tags("TopologyEntry", text)
    entries = [TopologyEntry.from_text(x) for x in topo_entries]
    phono_topo = {}
    for entry in entries:
      phono_topo.update({
        phone_id: entry
      for phone_id in entry.phone_ids})  
    
    return cls(entries, phono_topo)


@dataclass
class DiagGMM:
  gconsts: np.ndarray
  weights: np.ndarray
  means_invvars: np.ndarray
  inv_vars: np.ndarray

  @classmethod
  def from_text(cls, text):
    gconsts, text = consume_tag("GCONSTS", text)
    gconsts = gconsts[gconsts.find("[")+1:gconsts.find("]")]
    gconsts = np.array([float(x) for x in gconsts.split()])
    
    weights, text = consume_tag("WEIGHTS", text)
    weights = weights[weights.find("[")+1:weights.find("]")]
    weights = np.array([float(x) for x in weights.split()])

    means_invvars, text = consume_tag("MEANS_INVVARS", text)
    means_invvars = means_invvars[means_invvars.find("[")+1:means_invvars.find("]")]
    means_invvars = np.array([
                    [float(y) for y in x.strip().split()]
                     for x in means_invvars.strip().split("\n")])
    
    inv_vars, text = consume_tag("INV_VARS", text)
    inv_vars = inv_vars[inv_vars.find("[")+1:inv_vars.find("]")]
    inv_vars = np.array([
                    [float(y) for y in x.strip().split()]
                      for x in inv_vars.strip().split("\n")])
    
    return cls(gconsts, weights, means_invvars, inv_vars)

@dataclass     
class AcousticModel:
  ndim: int
  npdf: int
  gmm: List[DiagGMM]

  def __repr__(self):
    return f"AcousticModel({self.ndim}-dim, {self.npdf} PDFs, {len(self.gmm)} GMMs)"

  @classmethod
  def from_text(cls, text):
    pdf_idx = text.find("<DIMENSION>")
    assert pdf_idx > 0
    ac_text = text[pdf_idx:]
    ndim, ac_text = consume_tag("DIMENSION", ac_text)
    ndim = int(ndim)
    npdfs, ac_text = consume_tag("NUMPDFS", ac_text)
    npdfs = int(npdfs)

    gm_contents = find_tags("DiagGMM", ac_text)
    gmm = [DiagGMM.from_text(x) for x in gm_contents]

    return cls(ndim, npdfs, gmm)

@dataclass  
class TransitionModel:
  topo: HmmTopology
  triples: List[Tuple[int, int, int]]
  log_probs: np.ndarray
  am: AcousticModel
  tid2state: Dict[int, int] = field(default_factory=dict)
  state2tid: Dict[int, int] = field(default_factory=dict)
  tid2phone: Dict[int, int] = field(default_factory=dict)

  def __post_init__(self):
    self.generate_tids()

  def generate_tids(self):
    self.tid2state = {}
    self.state2tid = {}
    self.tid2phone = {}
    for trip_i, trip_x in enumerate(self.triples):      
      state_i = trip_i + 1      
      phone_id, hmm_state, fwd_pdf = trip_x
      topo = self.topo.phone_topo[phone_id]
      self.state2tid[state_i] = len(self.tid2state) + 1
      for trans_x in topo.hmm_states[hmm_state].transitions:
        tid = len(self.tid2state) + 1        
        self.tid2state[tid] = state_i        
        self.tid2phone[tid] = phone_id

  @classmethod
  def from_text(cls, text):
    # <Topology>
    topo_text = find_tags("Topology", text)[0]
    topo = HmmTopology.from_text(topo_text)

    # <Triples>
    triple_text = find_tags("Triples", text)
    n_triples, triple_text = consume_integer(triple_text[0])
    
    triples = []
    for triple_ln in triple_text.split("\n"):
      triple_ln.strip()
      trip = tuple(int(x) for x in triple_ln.split())
      if len(trip) == 3:
        triples.append(trip)

    # <LogProbs>
    log_prob_text = find_tags("LogProbs", text)[0]
    log_prob_text = log_prob_text[log_prob_text.find("[")+1:log_prob_text.find("]")]
    log_probs = np.array([float(x) for x in log_prob_text.split()])
    
    # DiagGMM
    am = AcousticModel.from_text(text)
    
    assert len(triples) == n_triples
    return cls(topo, triples, log_probs, am)
  

  
