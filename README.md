# ATFS

<br>

<p align="center">
<b>ATFS</b> - <b>A</b>ndroid <b>T</b>ooling <b>F</b>rom <b>S</b>cratch
<br>
<code>A learning journey into Android development tooling.</code>
</p>

<br>

---

👉 Read Chapter 1: https://github.com/hethon/ATFS/tree/master

---
## Chapter 2

**Replacing the manual build process with Gradle**

In [Chapter 1](https://github.com/hethon/ATFS/tree/master), we managed to build an Android app using a completely manual process. We ran each step one by one, until we finally produced a signed APK.

To make things easier, we grouped all those steps into a single script: `build.py`. This was a nice improvement. Instead of remembering every command and running them in the correct order, we could just run one script and let it execute each step perfectly.

But pretty quickly, a limitation became obvious.

The script isn’t *smart*. It just runs everything, every time. Even if I only change a single Java file, the script still runs all the build steps. This includes resource compilation, even when no XML files have been touched.

What if there was a build system that understands what changed, and *only* runs the necessary steps?

That’s where Gradle comes in.

### What is Gradle?

> Gradle is an open-source build automation tool used to manage the entire lifecycle of software development, including compiling, packaging, testing, and deployment.

For our purposes, we are mainly interested in how Gradle handles compiling and packaging.

What makes Gradle fundamentally different from our `build.py` script is that it is **intelligent**. It keeps track of "Inputs" and "Outputs," and decides which tasks actually need to run.

For example, if I only modify `MainActivity.java`, Gradle won’t bother recompiling the UI resources, because the input files for the resource compiler haven't changed. It simply reuses the previous outputs and continues from there. This is called an **Incremental Build**.

This kind of behavior might seem small right now, but it makes a massive difference as projects grow.

Of course, Gradle can do much more than this, and it’s not really fair to compare it to our simple Python script. But even this one advantage is enough for us to justify switching to it. We are not adopting Gradle just because "everyone else uses it"; we're adopting it because we have now experienced the limitations of doing everything manually.

### 1. Gradle Installation

I used [SDKMAN!](https://sdkman.io/install) to install the latest version of Gradle (version 9.4.1 at the time of writing) on my Linux machine.

To install SDKMAN, follow the instructions on their website: https://sdkman.io/install/

After installing SDKMAN, installing Gradle is as simple as running this one command:

> *(Note: You can drop the version number to install the latest version, but keeping it guarantees compatibility with this guide).*

```bash
sdk install gradle 9.4.1
```

Verify the installation:
```bash
gradle --version
```

### 2. Introducing Gradle to our project

At this point, our project looks like this:

- `src/` → our source code and resources
- `build/` → all generated outputs (classes, dex, APKs)
- `build.py` → a script that runs the entire build pipeline

Our goal is simple: **Replace `build.py` with Gradle build script.**


**A Note on the Language: Groovy vs. Kotlin**

Before we write our first Gradle file, we need to choose a language. Gradle build scripts can be written in two languages: Groovy (`build.gradle`) or Kotlin DSL (`build.gradle.kts`).

In this guide, we are going to use Groovy.

Whether you write your script in Groovy or Kotlin, Gradle builds the exact same graph in memory and executes the exact same steps. Our goal is to understand the concepts of build automation: inputs, outputs, task dependencies, and execution. Once you understand the concepts, switching the syntax later is trivial.

So, let's stick to Groovy and create our build file.

Let's create a file named `build.gradle` in the root of our project:

```bash
touch build.gradle
```

In our Python script, the very first thing we did was define our environment variables and paths. We can do the exact same thing at the top of our `build.gradle` file:

```groovy
// Read the ANDROID_HOME environment variable from your system
def androidHome = System.getenv("ANDROID_HOME")

if (androidHome == null) {
    throw new GradleException("ANDROID_HOME environment variable is not set!")
}

// Define the paths we need for our build tools
def buildTools = "${androidHome}/build-tools/34.0.0"
def platformJar = "${androidHome}/platforms/android-34/android.jar"

// Keystore configuration
def ksPassword = 'superSecret123'
def ksFileName = 'mykey.keystore'
def ksAlias = 'mykey'
```

> <br>
>
> ⚠️ **A note on Security:**
>
> You'll notice we defined our keystore password and alias directly in the script. While this is convenient for a learning project, **never do this in a professional or production environment.**
>
> Exposing your signing credentials in plain text is a security risk. In a real-world project, you would store these sensitive values in a `gradle.properties` file or an environment variable, and then instruct Gradle to read them from there. This allows you to exclude the secrets file from your Git repository (using `.gitignore`), keeping your passwords safe while still allowing the build system to access them.
>
> For our journey, hardcoding them keeps the focus on the **build process** rather than the security setup, but always keep this "Production-Ready" approach in the back of your mind!
>
> <br>

#### Writing our First Custom Task

In Gradle, everything is a Task. A task represents a single atomic piece of work for a build, such as compiling classes.

In our Python script, Step 1 was compiling our XML resources using `aapt2`:
```python
# The Python way
subprocess.check_call([
    f"{BUILD_TOOLS}/aapt2", "compile",
    "--dir", "src/main/res",
    "-o", "build/res"
])
```

Let's translate this into a Gradle task. Gradle has a built-in task type called Exec, which is specifically designed to run command-line tools. Add this to your `build.gradle`:
```groovy
tasks.register('compileResources', Exec) {
    inputs.dir file('src/main/res')
    outputs.dir file('build/res')

    doFirst {
        mkdir 'build/res'
    }

    commandLine "${buildTools}/aapt2", 'compile', '--dir', 'src/main/res', '-o', 'build/res'
}
```

Let's test our new build system. Open your terminal and run the task we just created:
```bash
gradle compileResources
```

You should see something like this:
```
BUILD SUCCESSFUL in 5s
1 actionable task: 1 executed
```

Gradle successfully ran `aapt2` and generated our compiled resources. So far, it feels exactly like our Python script. But here is where we see the difference. Run the exact same command a second time:
```bash
gradle compileResources
```

Output:
```
BUILD SUCCESSFUL in 744ms
1 actionable task: 1 up-to-date
```

**Notice the UP-TO-DATE text?**

Gradle didn't run the `aapt2` command. It finished in a far less amount of time, 744ms in my case.

Because we explicitly told Gradle what the inputs (`inputs.dir file('src/main/res')`) and outputs (`outputs.dir file('build/res')`) were, Gradle generated a cryptographic hash of those folders. On the second run, Gradle looked at the folders, realized nothing had changed, and completely skipped the task to save time.

This feature, **Incremental Build**, is the core reason build systems like Gradle exist.

### Chaining the rest of the Tasks
Right now, we have one task (`compileResources`). But our build process has 7 steps. If we write a task for each step, how does Gradle know what order to run them in?

In our Python script, the order was guaranteed because the code executed top-to-bottom. In Gradle, tasks don't run top-to-bottom. Instead, Gradle uses a Directed Acyclic Graph (DAG). We simply tell Gradle: "Task B depends on Task A." Gradle calculates the rest.

Let's translate the next few steps from our `build.py` script to see this in action. Add these to your `build.gradle`:

```groovy
tasks.register('linkResources', Exec) {
    dependsOn 'compileResources'

    inputs.dir file('build/res')
    inputs.file file('src/main/AndroidManifest.xml')

    outputs.dir file('build/generated')
    outputs.file file('build/unsigned.apk')

    doFirst {
        mkdir 'build/generated'
        args fileTree(dir: 'build/res', include: '*.flat').files
    }

    commandLine "${buildTools}/aapt2", 'link',
                '-I', platformJar,
                '--manifest', 'src/main/AndroidManifest.xml',
                '--java', 'build/generated',
                '-o', 'build/unsigned.apk'
}

tasks.register('compileJava', Exec) {
    dependsOn 'linkResources'

    inputs.dir file('src/main/java')
    inputs.dir file('build/generated')

    outputs.dir file('build/classes')

    doFirst {
        mkdir 'build/classes'
        args fileTree(dir: 'src/main/java', include: '**/*.java').files +
             fileTree(dir: 'build/generated', include: '**/*.java').files
    }

    commandLine 'javac', '-classpath', platformJar, '-d', 'build/classes'
}

tasks.register('convertToDex', Exec) {
    dependsOn 'compileJava'

    inputs.dir file('build/classes')

    outputs.dir file('build/dex')

    doFirst {
        mkdir 'build/dex'
        args fileTree(dir: 'build/classes', include: '**/*.class').files
    }

    commandLine "${buildTools}/d8", '--lib', platformJar, '--output', 'build/dex'
}

tasks.register('addDexToApk', Exec) {
    dependsOn 'convertToDex'

    inputs.file file('build/dex/classes.dex')
    inputs.file file('build/unsigned.apk')

    outputs.file file('build/unsigned_with_dex.apk')

    // Copy the original unsigned APK to the new name, then add the dex file
    doFirst {
        copy {
            from 'build/unsigned.apk'
            into 'build'
            rename { 'unsigned_with_dex.apk' }
        }
    }

    commandLine 'zip', '-j', 'build/unsigned_with_dex.apk', 'build/dex/classes.dex'
}

tasks.register('zipAlign', Exec) {
    dependsOn 'addDexToApk'

    inputs.file file('build/unsigned_with_dex.apk')

    outputs.file file('build/aligned.apk')

    commandLine "${buildTools}/zipalign", '-p', '-f', '4',
                'build/unsigned_with_dex.apk',
                'build/aligned.apk'
}

tasks.register('generateKeystore', Exec) {
    def keyalg = 'RSA'
    def validity = '10000'
    def dname = 'CN=Unknown, OU=Unknown, O=Unknown, L=Unknown, ST=Unknown, C=Unknown'

    inputs.property("ksPassword", ksPassword)
    inputs.property("ksFileName", ksFileName)
    inputs.property("ksAlias", ksAlias)
    inputs.property("keyalg", keyalg)
    inputs.property("validity", validity)
    inputs.property("dname", dname)

    outputs.file file(ksFileName)

    doFirst {
        file(ksFileName).delete()
    }

    commandLine 'keytool', '-genkeypair',
            '-keystore', ksFileName,
            '-alias', ksAlias,
            '-keyalg', keyalg,
            '-validity', validity,
            '-storepass', ksPassword,
            '-keypass', ksPassword,
            '-dname', dname
}

tasks.register('signApk', Exec) {
    dependsOn 'zipAlign', 'generateKeystore'

    inputs.file file('build/aligned.apk')
    inputs.file file(ksFileName)

    outputs.file file('build/signed.apk')

    commandLine "${buildTools}/apksigner", 'sign',
                '--ks', ksFileName,
                '--ks-key-alias', ksAlias,
                '--ks-pass', "pass:${ksPassword}",
                '--key-pass', "pass:${ksPassword}",
                '--out', 'build/signed.apk',
                'build/aligned.apk'
}
```

Once all 7 (+1 keystore generation task) tasks are registered and linked with `dependsOn`, you no longer have to worry about the order of operations.

If you want a final, signed APK, you simply open your terminal and ask Gradle to run the very last task in the chain:

```bash
gradle signApk
```

Gradle will look at `signApk` and say:
> *"To sign the APK, I first need to zipalign it. To align it, I need to package it. To package it, I need convertToDex... "*

It reads the chain all the way back to the beginning, checks the `inputs` and `outputs` of every single step, skips the ones that are `UP-TO-DATE`, and runs the ones that aren't.

We have successfully replaced our Python script with a much smarter, automated build system!


### What's Next?

Our `build.py` script was dumb. Our custom `build.gradle` is much better because it is incremental at the task level. If we change a `.java` file, Gradle is smart enough to skip `compileResources` and go straight to `compileJava`.

But there is a catch: **It is not incremental at the file level.**

If you have a project with `1,000` Java files and you change one line in one file, our `compileJava` task will blindly pass all `1,000` files to `javac` and recompile everything. On a massive enterprise app, this could take several minutes.

Could we fix this? Technically, yes. We could modify `build.gradle`, write a bunch of complex Groovy code using Gradle's internal file-tracking APIs to figure out exactly which file changed, and pass only that single file to the compiler.

But doing that for Java compilation, resource linking, and Dex conversion would require thousands of lines of code. Our simple build script would become massive, buggy, and impossible to maintain.

**What if we didn't have to write it ourselves?**

What if we could include something, a plugin, perhaps, that automatically injects tasks into our project? Tasks that are already perfectly configured, maintained by engineers at Google, and support true, lightning-fast, file-level incremental builds?

In the next chapter, we will replace our custom tasks and introduce the Android Gradle Plugin (AGP).
