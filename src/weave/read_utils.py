import re
from pathlib import Path

def find_tags(tag, text):    
    m = re.finditer(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return [x.group(1) for x in m]

def consume_tag(tag, text):
    text = text.strip()
    m = re.match(f"<{tag}>([^<]+)", text)
    if m:
        return m.group(1), text[m.end():]
    else:
        return "", text
    
def consume_integer(text):
    text = text.strip()
    m = re.match("^[0-9]+", text)
    if m:        
        return int(m.group(0)), text[m.end():]
    else:
        return None, text
    
def read_table(text):
    sym_dict = {}
    for row_x in text.split("\n"):    
        toks = row_x.split()
        
        if len(toks) < 2: continue
        sym_dict[toks[0]] = int(toks[1])
    return sym_dict

def read_wave_scp(data_dir):
    split_dir = data_dir / "split3"
    wavscps = {}
    # read wav.scp
    for wavscp_path in split_dir.glob("wav.*.scp"):
        lines = wavscp_path.read_text().split("\n")
        for ln in lines:
            fields = ln.split()
            if len(fields) < 2: continue
            utt_id = fields[0]
            wav_path = Path(fields[1]).stem
            wavscps[utt_id] = wav_path

    # read utt2spk.scp
    wav2utt = {}
    for utt2spk_path in split_dir.glob("utt2spk.*.scp"):
        lines = utt2spk_path.read_text().split("\n")
        for ln in lines:
            fields = ln.split()
            if len(fields) < 2: continue
            spk_id, utt_id = fields[0].split("-")
            if utt_id in wavscps:
                wav_path = wavscps[utt_id]
                wav2utt[wav_path] = fields[0]

    # sort utt2spk, just for convenience
    wav2utt = {k: v for k, v 
               in sorted(wav2utt.items(), key=lambda item: item[0])}
    return wav2utt