# ATFS

<br>

<p align="center">
<b>ATFS</b> - <b>A</b>ndroid <b>T</b>ooling <b>F</b>rom <b>S</b>cratch
<br>
<code>A learning journey into Android development tooling.</code>
</p>

<br>

---

Android Studio is a powerful tool. But when I first used it, much of what it did felt opaque, with endless Gradle syncs and auto-generated files that I barely understood.

I believe that to understand a tool, you must first understand the problem it solves. This project documents my journey learning Android development tooling. It begins by building a basic Android app using only the minimum necessary tools, without relying on an IDE or build system, and then introduces Gradle, followed by Android Studio.

## Goals
- Become comfortable with the Android tooling and development workflow.
- Understand what tools like Android Studio and Gradle handle automatically.
- Gain a clearer sense of how the pieces fit together.
- Develop a sense of control over the development process.


## Chapters of this Journey

This repository is structured into branches, each representing a chapter in the learning process.

- `chapter-1-manual-build` (📍You are here): Building an Android app using only the raw SDK command-line tools.

- [`chapter-2-gradle-cli`](https://github.com/hethon/atfs/tree/chapter-2-gradle-cli): Introducing Gradle and the Android Gradle Plugin to automate the build, still without an IDE. `[Not published yet]`

- [`chapter-3-android-studio`](https://github.com/hethon/atfs/tree/chapter-3-android-studio): Finally opening the IDE, with the magic stripped away and a full understanding of the underlying system. `[Not published yet]`

<br>

[⬇️ Go to the bottom](#whats-next)

## Chapter 1:

Building an Android app using only the raw SDK command-line tools.

**In this guide, we will manually:**
- Install and set up the components of the Android SDK.
- Create a directory layout.
- Write the application code and manifest.
- Run the correct terminal command for each compilation step until we get a signed, installable APK.
- Install the APK to a physical device using `adb`.

### Prerequisites
- JDK 17 is installed correctly, and the javac command is accessible globally.
- A Linux-based Terminal.

---

### 1. Installation and Setup

To build an app, we need the **Android SDK**. The Android SDK contains all the tools, libraries, and headers needed to compile Android code. 

The Android SDK consists of a handful of components. The most important one to start with is the `cmdline-tools` package. This package contains `sdkmanager`, which we will use to install the other components (like `build-tools`, `platform-tools`, etc.).

The `cmdline-tools` package is the minimal “bootstrap” package needed to:
1. Run `sdkmanager`.
2. Install everything else without needing the Android Studio GUI.

#### Step 1: Create the folder structure
Let's create a dedicated folder for our SDK.
```bash
mkdir -p ~/Android/cmdline-tools
cd ~/Android/cmdline-tools
```

#### Step 2: Download and unzip `cmdline-tools`
*(Note: You can check the [Android developer website](https://developer.android.com/studio#command-line-tools-only) for the latest download link).*
```bash
wget https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip

unzip commandlinetools-linux-14742923_latest.zip

mv cmdline-tools latest

rm commandlinetools-linux-14742923_latest.zip
```

After this, you will have `~/Android/cmdline-tools/latest/bin/`. Inside this `bin/` folder are the core tools like `sdkmanager`.

#### Step 3: Set environment variables
Add this to your `~/.bashrc` (or `~/.zshrc`):
```bash
export ANDROID_HOME=$HOME/Android
export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$PATH
```
Apply it:
```bash
source ~/.bashrc
```

You should now be able to run `sdkmanager` from anywhere:
```bash
sdkmanager --list
```

#### Step 4: Install the required SDK packages
From the list of available packages, we need three specific things to build an app:

*   **`build-tools`**: Includes tools like `aapt2` (resource compiler) and `d8` (bytecode converter) used to package your app into an APK.
*   **`platform-tools`**: Contains tools needed to communicate with physical or virtual devices (like `adb`).
*   **`platforms`**: The actual Android framework libraries (the `android.jar`) needed to compile your app against a specific version of Android. 

Run the following to install these packages (we are targeting Android API 34):
```bash
sdkmanager "build-tools;34.0.0" "platform-tools" "platforms;android-34"
```

Let's update our environment variables one more time to include the newly installed `platform-tools`:
```bash
export ANDROID_HOME=$HOME/Android
export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH
```
Apply it (`source ~/.bashrc`), and verify `adb` is accessible:
```bash
adb version
```

You might notice we only added `cmdline-tools` and `platform-tools` to PATH, but not `build-tools`. That’s intentional.

The tools inside `cmdline-tools` and `platform-tools` (`sdkmanager`, `adb`) are general-purpose commands you’ll run directly from the terminal, so it makes sense to have them globally available.

`build-tools`, on the other hand, is different. It contains the actual compilers and packaging tools (`aapt2`, `d8`, `apksigner`), and they live inside versioned directories, in our case, `$ANDROID_HOME/build-tools/34.0.0/`. Each Android project may require a specific version of these tools, and this project uses `34.0.0`.


In the next steps, we’ll invoke these tools using their full paths:

```
$ANDROID_HOME/build-tools/34.0.0/aapt2

# OR

$ANDROID_HOME/build-tools/34.0.0/d8

```

---

### 2. Creating the Project Structure

Let's create our workspace and the folders required to hold our code and the compiled outputs.

```bash
cd ~ # go back to home directory
mkdir HelloAndroid
cd HelloAndroid

mkdir -p src/main/java/com/example/hello
mkdir -p src/main/res/values
mkdir -p build/classes
mkdir -p build/dex
mkdir -p build/res
mkdir -p build/generated
```

**Why this specific structure?**
While we are building this manually, we are mirroring the standard directory structure expected by Gradle. `src/main/java` holds our logic, `src/main/res` holds our visuals, and the `build/` directory acts as our temporary workspace where our compiled binaries will go. Keeping this standard structure will make migrating to Gradle later incredibly easy.

#### Create a String Resource
In Android, the `res/` (resources) folder stores UI layouts, text, images, and colors. This keeps hardcoded strings out of our Java logic. 

```bash
touch src/main/res/values/strings.xml
```
**Content:**
```xml
<resources>
    <string name="app_name">HelloAndroid</string>
    <string name="welcome">Hey, welcome to my first app.</string>
</resources>
```
✅ **What this does:** It defines a string called `welcome`. Later, our Java code will reference this string via `R.string.welcome`.

#### Create the Activity (The app's entry point)
```bash
touch src/main/java/com/example/hello/MainActivity.java
```
**Content:**
```java
package com.example.hello;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        TextView text = new TextView(this);
        text.setText(R.string.welcome);
        
        setContentView(text);
    }
}
```

#### Create the AndroidManifest.xml
The Android OS does not scan your Java code to find out how your app works. It reads the Manifest. 

```bash
touch src/main/AndroidManifest.xml
```
**Content:**
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.hello"
    android:versionCode="1"
    android:versionName="1.0">

    <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="34" />

    <application android:label="@string/app_name">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
```
✅ **What this does:** It tells the OS what permissions the app needs, the name of the app, and crucially, the `MAIN` and `LAUNCHER` intent filters tell the OS: *"This Activity is the app's starting screen, put a clickable icon for it on the user's home screen."*

---

### 3. The Build Pipeline

This is where the magic is stripped away. We will run the exact terminal commands required to turn these text files into a working Android app.

#### Step 1: Compile Resources (`aapt2 compile`)
```bash
$ANDROID_HOME/build-tools/34.0.0/aapt2 compile \
    --dir src/main/res \
    -o build/res
```
👉 **What this does:** It reads our XML files, validates them for syntax errors, and converts them into compiled binary resources (`build/res/values_strings.arsc.flat`).

#### Step 2: Link Resources (`aapt2 link`)
```bash
$ANDROID_HOME/build-tools/34.0.0/aapt2 link \
  -I $ANDROID_HOME/platforms/android-34/android.jar \
  --manifest src/main/AndroidManifest.xml \
  --java build/generated \
  -o build/unsigned.apk \
  build/res/*.flat
```
👉 **What this does:** 
1. It packages our compiled resources and the Manifest into a brand new ZIP archive named `unsigned.apk`. (Yes, APK is just a ZIP archive with a strict internal structure enforced by Android.)

2. It generates the `R.java` file inside `build/generated`. The `R.java` file is the bridge that assigns a unique integer ID to our `<string name="welcome">`, allowing our Java code to call `R.string.welcome` without crashing!

#### Step 3: Compile the Java Code (`javac`)
We must compile our `MainActivity.java` and the newly generated `R.java` file together. We also must include the `android.jar` in our classpath, otherwise the compiler won't know what an `Activity` or a `TextView` is.

```bash
javac \
    -classpath $ANDROID_HOME/platforms/android-34/android.jar \
    -d build/classes \
    src/main/java/com/example/hello/*.java \
    build/generated/com/example/hello/*.java
```

This command compiles the Java codes and produces JVM bytecode `.class` files in `build/classes/com/example/hello`. Next, these `.class` files will be converted into Dalvik bytecode.

#### Step 4: Convert to Dalvik Bytecode (`d8`)
Android devices do not run standard Java `.class` files. They run highly optimized `.dex` (Dalvik Executable) files.

The `--lib` flag is similar to `-classpath` in `javac`, but specifically provides the Android framework `android.jar` so that `d8` can resolve references to Android APIs without packaging them into the final `DEX` output.

```bash
$ANDROID_HOME/build-tools/34.0.0/d8 \
    build/classes/com/example/hello/*.class \
    --lib $ANDROID_HOME/platforms/android-34/android.jar
    --output build/dex
```

We will now have a `build/dex/classes.dex` file.

#### Step 5: Add the Code to the APK
In Step 2, `aapt2` created `unsigned.apk` and put our resources in it. Now, we just inject our compiled code into that same ZIP archive.

```bash
zip -j build/unsigned.apk build/dex/classes.dex
```
*(The `-j` flag tells zip to drop the file at the root of the archive, which is exactly where Android expects `classes.dex` to be).*

#### Step 6: Zipalign
This step rearranges the uncompressed data inside the APK to sit on 4-byte boundaries. This allows the Android OS to read the app directly from memory (mmap) without having to extract it first, saving RAM.

```bash
$ANDROID_HOME/build-tools/34.0.0/zipalign -p -f 4 build/unsigned.apk build/aligned.apk
```

#### Step 7: Sign the APK
Android strictly requires every app to be cryptographically signed before it can be installed.

First, generate a keystore (we only need to do this once):
```bash
keytool -genkeypair \
  -keystore mykey.keystore \
  -alias mykey \
  -keyalg RSA \
  -validity 10000
```

Next, sign the aligned APK:
```bash
$ANDROID_HOME/build-tools/34.0.0/apksigner sign \
    --ks mykey.keystore \
    --ks-key-alias mykey \
    --out build/signed.apk \
    build/aligned.apk
```

**Yay! 🎉** We have manually assembled `build/signed.apk`. It is a fully valid Android application. Now we are ready to install it.

---

### 4. Install and Run

Let's put the app on a real phone using `adb` (Android Debug Bridge).

1. Enable **USB Debugging** in the Developer Settings of your phone.
2. Connect your phone to your PC. *(If you are using WSL, use `usbipd-win` to forward the USB connection to Linux).*
3. Verify the connection:
```bash
adb devices
```
*(If prompted on your phone, authorize the connection).*

4. Install the signed APK!
```bash
adb install -r build/signed.apk
```

Open your phone, go to your app drawer, and look for **HelloAndroid**. We just built and deployed an app entirely from the command line.

### 5. Automating the Process (`build.py`)

Typing these 7 terminal commands every time you change a single line of Java is exhausting. To make this process easily repeatable, I aggregated all of these steps into a Python script called `build.py`.

This script is roughly what `Gradle` and the `Android Gradle Plugin (AGP)` fundamentally do. They run `aapt2`, `javac`, and `d8` in the correct order, and output a signed APK.

Make sure you have `python3` installed and just give the script execute permissions and run it. It will do the 7 steps we did [above](#3-the-build-pipeline) and outputs `build/signed.apk`.

```bash
chmod +x build.py
./build.py
```
*(Note: It will prompt you for your keystore password during the signing step).*

---

### What's Next?

After successfully building this app manually, the logical next step is to invite **Gradle** and the **Android Gradle Plugin (AGP)** to the party. However, we are still going to keep **Android Studio** out of the picture for now. This will help us understand exactly how Gradle automates the manual steps we just learned.

> <br>
>
> **Side Note**
>
> At this point you can take a detour and try to learn Gradle on a pure Java project first. This helps you understand Gradle's core concepts without the added noise of the Android SDK. 
>
> That is exactly what I did. I picked up an old Java Swing Calculator app I made a while ago and migrated it to Gradle. It started a massive chain of rabbit holes and I ended up learning a lot of other cool things. You can check that out here: https://github.com/hethon/Kasio.
>
> <br>


To keep this branch as a pure, Gradle-free reference, the Gradle implementation will be documented in a separate branch here: https://github.com/hethon/atfs/tree/chapter-2-gradle-cli. 

<br>

[⬆️ Go to Up](#atfs)
