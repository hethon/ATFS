#!/usr/bin/env python3

import os
import getpass
import subprocess
from pathlib import Path

# ---------------- CONFIG ----------------
android_home_env = os.environ.get("ANDROID_HOME")
if not android_home_env:
    print("ERROR: ANDROID_HOME environment variable is not set.")

ANDROID_HOME = Path(android_home_env)
BUILD_TOOLS = ANDROID_HOME / "build-tools" / "34.0.0"
PLATFORM_JAR = Path(ANDROID_HOME) / "platforms/android-34/android.jar"

PROJECT_ROOT = Path(".")
SRC_DIR = PROJECT_ROOT / "src"
RES_DIR = SRC_DIR / "main" / "res"
BUILD_DIR = PROJECT_ROOT / "build"
GENERATED_DIR = BUILD_DIR / "generated"
CLASSES_DIR = BUILD_DIR / "classes"
DEX_DIR = BUILD_DIR / "dex"
APK_NAME = "HelloAndroid.apk"
KEYSTORE = PROJECT_ROOT / "mykey.keystore"
KEY_ALIAS = "mykey"
MANIFEST = SRC_DIR / "main" / "AndroidManifest.xml"
# ----------------------------------------

def run(cmd, **kwargs):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, **kwargs)

def main():
    # ---------------- Handle Keystore ----------------
    if not KEYSTORE.exists():
        print(f"Keystore '{KEYSTORE.name}' not found. Generating a new one...")
        ks_pass = getpass.getpass("Enter a NEW password for the keystore: ")

        # We use -dname to prevent keytool from asking interactive questions (Name, Org, etc.)
        # We use -storepass and -keypass to pass the password automatically
        run([
            "keytool", "-genkeypair",
            "-keystore", str(KEYSTORE),
            "-alias", KEY_ALIAS,
            "-keyalg", "RSA",
            "-validity", "10000",
            "-storepass", ks_pass,
            "-keypass", ks_pass,
            "-dname", "CN=Unknown, OU=Unknown, O=Unknown, L=Unknown, ST=Unknown, C=Unknown"
        ])
        print("Keystore generated successfully.\n")
    else:
        ks_pass = getpass.getpass("Enter keystore password: ")

    # Make build dirs
    for d in [BUILD_DIR, GENERATED_DIR, CLASSES_DIR, DEX_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # ---------------- Step 1: Compile resources ----------------
    res_flat_dir = BUILD_DIR / "res"
    res_flat_dir.mkdir(exist_ok=True)
    run([
        f"{BUILD_TOOLS}/aapt2",
        "compile",
        "--dir", str(RES_DIR),
        "-o", str(res_flat_dir)
    ])

    # ---------------- Step 2: Link resources + manifest ----------------
    run([
        f"{BUILD_TOOLS}/aapt2",
        "link",
        "-I", str(PLATFORM_JAR),
        "--manifest", str(MANIFEST),
        "--java", str(GENERATED_DIR),
        "-o", str(BUILD_DIR / "unsigned.apk"),
        *(str(f) for f in res_flat_dir.glob("*.flat"))
    ])

    # ---------------- Step 3: Compile Java ----------------
    java_files = list(GENERATED_DIR.rglob("*.java")) + list(SRC_DIR.rglob("*.java"))
    run([
        "javac",
        "-classpath", str(PLATFORM_JAR),
        "-d", str(CLASSES_DIR),
        *(str(f) for f in java_files)
    ])

    # ---------------- Step 4: Convert to DEX ----------------
    run([
        f"{BUILD_TOOLS}/d8",
        *(str(f) for f in CLASSES_DIR.rglob("*.class")),
        "--lib", str(PLATFORM_JAR),
        "--output", str(DEX_DIR)
    ])

    # ---------------- Step 5: Add classes.dex to APK ----------------
    dex_file = DEX_DIR / "classes.dex"
    # ADDED '-j' (junk paths) so classes.dex is placed at the root of the APK
    run(["zip", "-j", str(BUILD_DIR / "unsigned.apk"), str(dex_file)])

    # ---------------- Step 6: Zipalign (REQUIRED for Android 11+) ---
    aligned_apk = BUILD_DIR / "aligned.apk"
    run([
        f"{BUILD_TOOLS}/zipalign",
        "-p", "-f", "4",
        str(BUILD_DIR / "unsigned.apk"),
        str(aligned_apk)
    ])

    # ---------------- Step 7: Sign APK ----------------
    signed_apk = BUILD_DIR / "signed.apk"
    run([
        f"{BUILD_TOOLS}/apksigner",
        "sign",
        "--ks", str(KEYSTORE),
        "--ks-key-alias", KEY_ALIAS, 
        "--ks-pass", f"pass:{ks_pass}",
        "--key-pass", f"pass:{ks_pass}",
        "--out", str(signed_apk),
        str(aligned_apk)
    ])

    print(f"Build complete! Signed APK at {signed_apk}")

if __name__ == "__main__":
    main()
