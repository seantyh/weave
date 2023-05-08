import re

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
