import sys, os, glob, re

title_id = sys.argv[1] if len(sys.argv) > 1 else "PCSE00120"
print("[*] Menyuntikkan Optimasi Compiler Snapdragon 680 (Kryo 265 Cortex-A73/A53) ke CMakeLists.txt...")

cmake_path = "vpk_src/CMakeLists.txt"
if os.path.exists(cmake_path):
    with open(cmake_path, "r", encoding="utf-8") as f:
        cmake = f.read()
    sd680_flags = """
if(ANDROID)
    add_compile_options(-O3 -ffast-math -fno-finite-math-only -fomit-frame-pointer -march=armv8-a+crc+crypto -mcpu=cortex-a73.cortex-a53 -mtune=cortex-a73.cortex-a53)
    add_link_options(-Wl,-O3 -Wl,--gc-sections)
endif()
"""
    cmake = cmake + "\n" + sd680_flags
    with open(cmake_path, "w", encoding="utf-8") as f:
        f.write(cmake)

# Patch Kotlin / Java getArguments() di source android/
for kt_file in glob.glob("vpk_src/android/**/*.kt", recursive=True):
    with open(kt_file, "r", encoding="utf-8") as f:
        kt = f.read()
    if "getArguments" in kt or "SDLActivity" in kt:
        if "override fun getArguments" in kt:
            kt = re.sub(
                r'override\s+fun\s+getArguments\(\)\s*:\s*Array<String>\s*\{[^}]*\}',
                f'override fun getArguments(): Array<String> {{ return arrayOf("-r", "{title_id}") }}',
                kt
            )
        else:
            kt = kt.rsplit("}", 1)[0] + f'\n    override fun getArguments(): Array<String> = arrayOf("-r", "{title_id}")\n}}\n'
        with open(kt_file, "w", encoding="utf-8") as f:
            f.write(kt)

for java_file in glob.glob("vpk_src/android/**/SDLActivity.java", recursive=True):
    with open(java_file, "r", encoding="utf-8") as f:
        jv = f.read()
    jv = re.sub(
        r'protected\s+String\[\]\s+getArguments\(\)\s*\{[^}]*\}',
        f'protected String[] getArguments() {{ return new String[]{{"-r", "{title_id}"}}; }}',
        jv
    )
    with open(java_file, "w", encoding="utf-8") as f:
        f.write(jv)

# Kunci ABI hanya ke arm64-v8a agar build 2x lebih cepat & ringan
for gradle_file in glob.glob("vpk_src/android/**/build.gradle*", recursive=True):
    with open(gradle_file, "r", encoding="utf-8") as f:
        gr = f.read()
    gr = gr.replace('"x86_64"', '').replace("'x86_64'", '').replace(', "x86_64"', '')
    with open(gradle_file, "w", encoding="utf-8") as f:
        f.write(gr)

print("[+] Source code nckstwrt/Vita3K-Plus berhasil di-patch untuk Snapdragon 680!")
