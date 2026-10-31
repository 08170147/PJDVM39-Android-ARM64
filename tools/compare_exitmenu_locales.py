#!/usr/bin/env python3
"""Compare ExitMenu TXP type-2 texture payloads across localized IPA folders.

This reports byte-level differences only; it does not infer sprite or language semantics.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, struct, zipfile
from pathlib import PurePosixPath

LANGS = ("cn", "tw", "kr", "jp", "en")
REL = "rom_switch/rom/2d/spr_nswgam_menu.farc"

def read_bin(ipa: zipfile.ZipFile, lang: str) -> bytes:
    suffix = f"/ExitMenu/{lang}/{REL}"
    matches = [n for n in ipa.namelist() if n.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"{lang}: expected one {suffix}, found {len(matches)}")
    raw = ipa.read(matches[0])
    if raw[:4] != b"FArC" or len(raw) < 0x30:
        raise ValueError(f"{lang}: unexpected FArC header")
    name_len = struct.unpack_from(">I", raw, 8)[0]
    data_off = 0x24 + name_len
    if data_off >= len(raw) or raw[data_off:data_off+2] != b"\x1f\x8b":
        # Build 19 observed container stores the gzip member at 0x30.
        data_off = 0x30
    data = gzip.decompress(raw[data_off:])
    return data

def records(data: bytes) -> list[dict]:
    offsets=[]; cur=0
    while True:
        p=data.find(b"TXP",cur)
        if p<0: break
        offsets.append(p); cur=p+1
    result=[]
    for p in offsets:
        if p+4>len(data) or data[p+3]!=2: continue
        nxt=next((q for q in offsets if q>p),len(data))
        if p+24>nxt: raise ValueError(f"truncated TXP2 at {p:#x}")
        w=struct.unpack_from("<H",data,p+4)[0]
        h=struct.unpack_from("<H",data,p+8)[0]
        fmt=struct.unpack_from("<I",data,p+12)[0]
        payload=data[p+24:nxt]
        result.append({"index":len(result),"offset":p,"width":w,"height":h,
                       "format_id":fmt,"payload_bytes":len(payload),
                       "sha256":hashlib.sha256(payload).hexdigest()})
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ipa")
    ap.add_argument("--out",default="exitmenu_locale_comparison.json")
    args=ap.parse_args()
    output={}
    with zipfile.ZipFile(args.ipa) as ipa:
        for lang in LANGS:
            data=read_bin(ipa,lang)
            output[lang]={"bin_bytes":len(data),"bin_sha256":hashlib.sha256(data).hexdigest(),
                          "records":records(data)}
    reference=output["en"]["records"]
    for lang,info in output.items():
        if len(info["records"])!=len(reference):
            raise ValueError(f"{lang}: record count differs from English")
        for a,b in zip(reference,info["records"]):
            if (a["index"],a["offset"],a["width"],a["height"],a["format_id"]) != (b["index"],b["offset"],b["width"],b["height"],b["format_id"]):
                raise ValueError(f"{lang}: structural record mismatch at index {a['index']}")
        info["payload_diff_indexes_vs_en"]=[a["index"] for a,b in zip(reference,info["records"]) if a["sha256"]!=b["sha256"]]
    result={"reference_language":"en","languages":output,
            "notes":["Byte-level comparison only; differing payloads are not automatically classified as translated text.",
                     "TXP record layout and dimensions are required to match English before hashes are compared.",
                     "Observed format_id is reported without assigning undocumented engine semantics."]}
    with open(args.out,"w",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:{"bin_bytes":v["bin_bytes"],"record_count":len(v["records"]),
                         "diff_indexes_vs_en":v["payload_diff_indexes_vs_en"]} for k,v in output.items()},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
