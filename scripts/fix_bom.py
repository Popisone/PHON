from pathlib import Path

examples = Path(r"C:\Projects\PHON\examples")
for name in ["alu8.phon", "while_test.phon"]:
    p = examples / name
    if not p.exists():
        print(f"  {name}: not found")
        continue
    raw = p.read_bytes()
    has_bom = raw[:3] == b"\xef\xbb\xbf"
    if not has_bom:
        print(f"  {name}: no BOM (already clean)")
        continue
    # Read with utf-8-sig (strips BOM), write with utf-8 (no BOM)
    text = p.read_text(encoding="utf-8-sig")
    p.write_text(text, encoding="utf-8")
    print(f"  {name}: BOM stripped")
