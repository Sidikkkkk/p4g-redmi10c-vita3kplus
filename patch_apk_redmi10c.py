import sys, os, glob, re, shutil
from PIL import Image, ImageDraw

title_id = sys.argv[1] if len(sys.argv) > 1 else "PCSE00120"

print("[*] Mem-patch AndroidManifest.xml untuk Redmi 10C (Zero-Copy mmap + largeHeap + GameMode)...")
manifest_path = "decompiled/AndroidManifest.xml"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = f.read()

manifest = re.sub(r'android:label="[^"]*"', 'android:label="Persona 4 Golden"', manifest)
for attr in ["extractNativeLibs", "largeHeap", "isGame", "appCategory", "hardwareAccelerated"]:
    manifest = re.sub(rf'\s*android:{attr}="[^"]*"', '', manifest)

redmi10c_flags = (
    '<application '
    'android:isGame="true" '
    'android:appCategory="game" '
    'android:largeHeap="true" '
    'android:hardwareAccelerated="true" '
    'android:extractNativeLibs="false" '
)
manifest = manifest.replace('<application ', redmi10c_flags, 1)
manifest = re.sub(r'android:screenOrientation="[^"]*"', 'android:screenOrientation="sensorLandscape"', manifest)

with open(manifest_path, "w", encoding="utf-8") as f:
    f.write(manifest)

# Pastikan lib/*.so tidak dikompresi agar langsung di-mmap ke RAM LPDDR4X Redmi 10C
yml_path = "decompiled/apktool.yml"
if os.path.exists(yml_path):
    with open(yml_path, "r", encoding="utf-8") as f:
        yml = f.read()
    if "doNotCompress:" in yml and "- so" not in yml:
        yml = yml.replace("doNotCompress:", "doNotCompress:\n- so")
    with open(yml_path, "w", encoding="utf-8") as f:
        f.write(yml)

# Ubah strings.xml
for s_file in glob.glob("decompiled/res/values*/strings.xml"):
    with open(s_file, "r", encoding="utf-8") as f:
        st = f.read()
    st = re.sub(r'(<string name="app_name"[^>]*>).*?(</string>)', r'\1Persona 4 Golden\2', st)
    with open(s_file, "w", encoding="utf-8") as f:
        f.write(st)

print(f"[*] Menyuntikkan Direct-Boot (-r {title_id}) ke Smali Kotlin/Java nckstwrt/Vita3K-Plus...")
target_smalis = []
for root, _, files in os.walk("decompiled"):
    for file in files:
        if file in ("Emulator.smali", "SDLActivity.smali"):
            target_smalis.append(os.path.join(root, file))

patch_method = f"""
.method protected getArguments()[Ljava/lang/String;
    .locals 3
    const/4 v0, 0x2
    new-array v0, v0, [Ljava/lang/String;
    const/4 v1, 0x0
    const-string v2, "-r"
    aput-object v2, v0, v1
    const/4 v1, 0x1
    const-string v2, "{title_id}"
    aput-object v2, v0, v1
    return-object v0
.end method
"""

pattern = re.compile(r'\.method\s+(?:protected|public)\s+getArguments\(\)\[Ljava/lang/String;.*?\.end method', re.DOTALL)

for smali_path in target_smalis:
    with open(smali_path, "r", encoding="utf-8") as f:
        code = f.read()
    if pattern.search(code):
        code = pattern.sub(patch_method.strip(), code)
    else:
        code += "\n" + patch_method
    with open(smali_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f" -> Direct-Boot berhasil diinjeksi ke: {smali_path}")

print("[*] Membuat & Mengganti Ikon Persona 4 Golden...")
for xml_dir in glob.glob("decompiled/res/mipmap-anydpi*"):
    shutil.rmtree(xml_dir, ignore_errors=True)

def make_icon(sz):
    img = Image.new("RGBA", (sz, sz), (255, 215, 0, 255))
    drw = ImageDraw.Draw(img)
    sw = max(4, sz // 16)
    for i, col in enumerate([(255, 140, 0, 255), (225, 35, 20, 255), (20, 20, 20, 255)]):
        x0 = sz - (i + 2) * sw * 1.5
        drw.polygon([(x0, 0), (x0 + sw, 0), (x0 - sw * 2, sz), (x0 - sw * 3, sz)], fill=col)
    b = max(4, sz // 24)
    drw.rectangle([b, b, sz - b, sz - b], outline=(15, 15, 15, 255), width=b)
    p = sz // 5
    drw.rectangle([p, p, sz - p, sz - p], fill=(15, 15, 15, 255))
    return img

for ic in glob.glob("decompiled/res/mipmap*/*launcher*.*") + glob.glob("decompiled/res/drawable*/*launcher*.*"):
    if ic.endswith((".png", ".webp")):
        try:
            with Image.open(ic) as im:
                sz = im.size[0]
            out = make_icon(sz)
            out.save(ic, "WEBP" if ic.endswith(".webp") else "PNG")
        except Exception:
            pass
