# pesaZaShambaApp.py
# ------------------------------------------------------------
# This script generates a complete Android Studio project:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
#
# It copies your app logo from:
#   C:\Users\kirwa\Documents\coding\codeScripts\peza_za_shamba_logo.png
#
# How to run in PowerShell:
#   cd C:\Users\kirwa\Documents\coding\codeScripts
#   python .\pesaZaShambaApp.py
#
# Then open this folder in Android Studio:
#   C:\Users\kirwa\AndroidStudioProjects\PesaZaShambaApp
# ------------------------------------------------------------

from pathlib import Path
import shutil
import textwrap
import sys


PROJECT_NAME = "PesaZaShambaApp"
LOGO_SOURCE = Path(r"C:\Users\kirwa\Documents\coding\codeScripts\peza_za_shamba_logo.png")
OUTPUT_ROOT = Path(r"C:\Users\kirwa\AndroidStudioProjects")
PROJECT_DIR = OUTPUT_ROOT / PROJECT_NAME

APP_DIR = PROJECT_DIR / "app"
MAIN_DIR = APP_DIR / "src" / "main"
KOTLIN_DIR = MAIN_DIR / "java" / "com" / "kirwa" / "pesazashamba"
RES_DIR = MAIN_DIR / "res"
DRAWABLE_DIR = RES_DIR / "drawable"
MIPMAP_DIR = RES_DIR / "mipmap-hdpi"
VALUES_DIR = RES_DIR / "values"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def create_project_structure() -> None:
    for folder in [PROJECT_DIR, APP_DIR, MAIN_DIR, KOTLIN_DIR, DRAWABLE_DIR, MIPMAP_DIR, VALUES_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def copy_logo() -> None:
    destination = DRAWABLE_DIR / "pesa_za_shamba_logo.png"

    if LOGO_SOURCE.exists():
        shutil.copy2(LOGO_SOURCE, destination)
        print(f"[OK] Logo copied to: {destination}")
    else:
        print("[WARNING] Logo was not found at:")
        print(f"          {LOGO_SOURCE}")
        print("[INFO] A placeholder vector logo will be created instead.")
        print("[INFO] Later, manually copy your real logo to:")
        print(f"       {destination}")

        write_file(DRAWABLE_DIR / "pesa_za_shamba_logo.xml", """
            <vector xmlns:android="http://schemas.android.com/apk/res/android"
                android:width="160dp"
                android:height="160dp"
                android:viewportWidth="160"
                android:viewportHeight="160">
                <path
                    android:fillColor="#0B5D4F"
                    android:pathData="M80,8a72,72 0,1 0,0.1 0M80,20a60,60 0,1 1,-0.1 0" />
                <path
                    android:fillColor="#2E7D32"
                    android:pathData="M32,100 L58,70 L76,88 L122,38 L132,48 L77,111 L59,93 L42,111z" />
                <path
                    android:fillColor="#F4F8EE"
                    android:pathData="M48,118h64v8H48z" />
            </vector>
        """)


def create_gradle_files() -> None:
    write_file(PROJECT_DIR / "settings.gradle.kts", """
        pluginManagement {
            repositories {
                google()
                mavenCentral()
                gradlePluginPortal()
            }
        }

        dependencyResolutionManagement {
            repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
            repositories {
                google()
                mavenCentral()
            }
        }

        rootProject.name = "PesaZaShambaApp"
        include(":app")
    """)

    write_file(PROJECT_DIR / "build.gradle.kts", """
        plugins {
            id("com.android.application") version "8.7.3" apply false
            id("org.jetbrains.kotlin.android") version "2.0.21" apply false
            id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
        }
    """)

    write_file(APP_DIR / "build.gradle.kts", """
        plugins {
            id("com.android.application")
            id("org.jetbrains.kotlin.android")
            id("org.jetbrains.kotlin.plugin.compose")
        }

        android {
            namespace = "com.kirwa.pesazashamba"
            compileSdk = 35

            defaultConfig {
                applicationId = "com.kirwa.pesazashamba"
                minSdk = 23
                targetSdk = 35
                versionCode = 1
                versionName = "1.0"
            }

            buildFeatures {
                compose = true
            }

            packaging {
                resources {
                    excludes += "/META-INF/{AL2.0,LGPL2.1}"
                }
            }
        }

        dependencies {
            val composeBom = platform("androidx.compose:compose-bom:2024.10.00")
            implementation(composeBom)
            androidTestImplementation(composeBom)

            implementation("androidx.core:core-ktx:1.15.0")
            implementation("androidx.activity:activity-compose:1.9.3")
            implementation("androidx.compose.ui:ui")
            implementation("androidx.compose.ui:ui-graphics")
            implementation("androidx.compose.ui:ui-tooling-preview")
            implementation("androidx.compose.material3:material3")
            implementation("androidx.compose.material:material-icons-extended")
            implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")

            debugImplementation("androidx.compose.ui:ui-tooling")
            debugImplementation("androidx.compose.ui:ui-test-manifest")
        }
    """)

    write_file(PROJECT_DIR / "gradle.properties", """
        org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
        android.useAndroidX=true
        kotlin.code.style=official
        android.nonTransitiveRClass=true
    """)


def create_android_manifest() -> None:
    write_file(MAIN_DIR / "AndroidManifest.xml", """
        <manifest xmlns:android="http://schemas.android.com/apk/res/android">
            <application
                android:allowBackup="true"
                android:icon="@mipmap/ic_launcher"
                android:label="Pesa Za Shamba"
                android:roundIcon="@mipmap/ic_launcher_round"
                android:supportsRtl="true"
                android:theme="@style/Theme.PesaZaShamba">
                <activity
                    android:name=".MainActivity"
                    android:exported="true">
                    <intent-filter>
                        <action android:name="android.intent.action.MAIN" />
                        <category android:name="android.intent.category.LAUNCHER" />
                    </intent-filter>
                </activity>
            </application>
        </manifest>
    """)


def create_resource_files() -> None:
    write_file(VALUES_DIR / "colors.xml", """
        <resources>
            <color name="deep_forest">#064C43</color>
            <color name="farm_green">#2E7D32</color>
            <color name="light_green">#EAF5EA</color>
            <color name="cream">#FFFDF3</color>
        </resources>
    """)

    write_file(VALUES_DIR / "strings.xml", """
        <resources>
            <string name="app_name">Pesa Za Shamba</string>
        </resources>
    """)

    write_file(VALUES_DIR / "themes.xml", """
        <resources>
            <style name="Theme.PesaZaShamba" parent="android:style/Theme.Material.Light.NoActionBar">
                <item name="android:windowLightStatusBar">true</item>
                <item name="android:statusBarColor">#FFFDF3</item>
                <item name="android:navigationBarColor">#FFFDF3</item>
            </style>
        </resources>
    """)

    write_file(MIPMAP_DIR / "ic_launcher.xml", """
        <vector xmlns:android="http://schemas.android.com/apk/res/android"
            android:width="48dp"
            android:height="48dp"
            android:viewportWidth="48"
            android:viewportHeight="48">
            <path android:fillColor="#064C43" android:pathData="M24,2a22,22 0,1 0,0.1 0"/>
            <path android:fillColor="#FFFFFF" android:pathData="M12,30 L20,21 L25,26 L36,14 L39,17 L25,33 L20,28 L15,34z"/>
        </vector>
    """)

    write_file(MIPMAP_DIR / "ic_launcher_round.xml", """
        <vector xmlns:android="http://schemas.android.com/apk/res/android"
            android:width="48dp"
            android:height="48dp"
            android:viewportWidth="48"
            android:viewportHeight="48">
            <path android:fillColor="#064C43" android:pathData="M24,2a22,22 0,1 0,0.1 0"/>
            <path android:fillColor="#FFFFFF" android:pathData="M12,30 L20,21 L25,26 L36,14 L39,17 L25,33 L20,28 L15,34z"/>
        </vector>
    """)


def create_main_activity() -> None:
    write_file(KOTLIN_DIR / "MainActivity.kt", """
        package com.kirwa.pesazashamba

        import android.os.Bundle
        import android.widget.Toast
        import androidx.activity.ComponentActivity
        import androidx.activity.compose.setContent
        import androidx.compose.foundation.Image
        import androidx.compose.foundation.background
        import androidx.compose.foundation.layout.*
        import androidx.compose.foundation.rememberScrollState
        import androidx.compose.foundation.shape.RoundedCornerShape
        import androidx.compose.foundation.text.KeyboardOptions
        import androidx.compose.foundation.verticalScroll
        import androidx.compose.material.icons.Icons
        import androidx.compose.material.icons.filled.Agriculture
        import androidx.compose.material.icons.filled.ArrowBack
        import androidx.compose.material.icons.filled.Calculate
        import androidx.compose.material.icons.filled.Grass
        import androidx.compose.material.icons.filled.LocalDrink
        import androidx.compose.material.icons.filled.Lock
        import androidx.compose.material.icons.filled.Person
        import androidx.compose.material3.*
        import androidx.compose.runtime.*
        import androidx.compose.ui.Alignment
        import androidx.compose.ui.Modifier
        import androidx.compose.ui.graphics.Brush
        import androidx.compose.ui.graphics.Color
        import androidx.compose.ui.graphics.vector.ImageVector
        import androidx.compose.ui.res.painterResource
        import androidx.compose.ui.text.font.FontWeight
        import androidx.compose.ui.text.input.KeyboardType
        import androidx.compose.ui.text.input.PasswordVisualTransformation
        import androidx.compose.ui.text.style.TextAlign
        import androidx.compose.ui.unit.dp
        import java.text.NumberFormat
        import java.text.SimpleDateFormat
        import java.util.Date
        import java.util.Locale

        class MainActivity : ComponentActivity() {
            override fun onCreate(savedInstanceState: Bundle?) {
                super.onCreate(savedInstanceState)

                setContent {
                    PesaZaShambaTheme {
                        PesaZaShambaApp(
                            showMessage = { message ->
                                Toast.makeText(this, message, Toast.LENGTH_LONG).show()
                            }
                        )
                    }
                }
            }
        }

        enum class Screen {
            Login,
            Selection,
            Dairy,
            Maize,
            Records
        }

        data class ExpenseRecord(
            val category: String,
            val total: Double,
            val date: String,
            val items: Map<String, String>
        )

        val DeepForest = Color(0xFF064C43)
        val FarmGreen = Color(0xFF2E7D32)
        val Cream = Color(0xFFFFFDF3)
        val SoftGreen = Color(0xFFEAF5EA)

        @Composable
        fun PesaZaShambaTheme(content: @Composable () -> Unit) {
            val colors = lightColorScheme(
                primary = DeepForest,
                secondary = FarmGreen,
                background = Cream,
                surface = Color.White,
                onPrimary = Color.White,
                onSecondary = Color.White,
                onBackground = DeepForest,
                onSurface = DeepForest
            )

            MaterialTheme(
                colorScheme = colors,
                content = content
            )
        }

        @Composable
        fun PesaZaShambaApp(showMessage: (String) -> Unit) {
            var currentScreen by remember { mutableStateOf(Screen.Login) }
            val records = remember { mutableStateMapOf<String, ExpenseRecord>() }

            Surface(
                modifier = Modifier.fillMaxSize(),
                color = Cream
            ) {
                when (currentScreen) {
                    Screen.Login -> LoginScreen(
                        onLoginSuccess = { currentScreen = Screen.Selection }
                    )

                    Screen.Selection -> SelectionScreen(
                        onDairySelected = { currentScreen = Screen.Dairy },
                        onMaizeSelected = { currentScreen = Screen.Maize },
                        onRecordsSelected = { currentScreen = Screen.Records }
                    )

                    Screen.Dairy -> ExpenseFormScreen(
                        title = "Dairy Expenses",
                        subtitle = "Track daily and monthly dairy costs",
                        icon = Icons.Default.LocalDrink,
                        fields = listOf(
                            "Monthly Salary",
                            "Transportation",
                            "Tick Spray",
                            "Deworming",
                            "AI"
                        ),
                        submitButtonText = "Submit Dairy Record",
                        onBack = { currentScreen = Screen.Selection },
                        onSubmit = { record ->
                            val key = "Dairy-" + System.currentTimeMillis()
                            records[key] = record
                            showMessage("Dairy record saved. Total: " + formatKes(record.total))
                        }
                    )

                    Screen.Maize -> ExpenseFormScreen(
                        title = "Maize Expenses",
                        subtitle = "Track land preparation, spray, fertilizer and transport",
                        icon = Icons.Default.Grass,
                        fields = listOf(
                            "Tractor Fuel",
                            "Driver Salary",
                            "Herbicide",
                            "Insecticide",
                            "Foliar Spray",
                            "Urea",
                            "CAN",
                            "Maize Transport",
                            "Loading Maize",
                            "Unloading Maize"
                        ),
                        submitButtonText = "Submit Maize Record",
                        onBack = { currentScreen = Screen.Selection },
                        onSubmit = { record ->
                            val key = "Maize-" + System.currentTimeMillis()
                            records[key] = record
                            showMessage("Maize record saved. Total: " + formatKes(record.total))
                        }
                    )

                    Screen.Records -> RecordsScreen(
                        records = records.values.toList().reversed(),
                        onBack = { currentScreen = Screen.Selection }
                    )
                }
            }
        }

        @Composable
        fun LogoImage(modifier: Modifier = Modifier) {
            Image(
                painter = painterResource(id = R.drawable.pesa_za_shamba_logo),
                contentDescription = "Pesa Za Shamba Logo",
                modifier = modifier
            )
        }

        @Composable
        fun AppBackground(content: @Composable () -> Unit) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        Brush.verticalGradient(
                            colors = listOf(
                                Cream,
                                SoftGreen,
                                Color(0xFFDDEFD8)
                            )
                        )
                    )
            ) {
                content()
            }
        }

        @Composable
        fun LoginScreen(onLoginSuccess: () -> Unit) {
            var username by remember { mutableStateOf("") }
            var password by remember { mutableStateOf("") }

            AppBackground {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    LogoImage(
                        modifier = Modifier
                            .size(210.dp)
                            .padding(bottom = 4.dp)
                    )

                    Text(
                        text = "Pesa Za Shamba",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.ExtraBold,
                        color = DeepForest
                    )

                    Text(
                        text = "Farm Expense Tracker for Kesses Farmers",
                        style = MaterialTheme.typography.bodyLarge,
                        color = FarmGreen,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(26.dp))

                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(28.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
                    ) {
                        Column(
                            modifier = Modifier.padding(22.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "Login",
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                                color = DeepForest
                            )

                            Spacer(modifier = Modifier.height(16.dp))

                            OutlinedTextField(
                                value = username,
                                onValueChange = { username = it },
                                label = { Text("Username or Phone Number") },
                                leadingIcon = {
                                    Icon(Icons.Default.Person, contentDescription = null)
                                },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(12.dp))

                            OutlinedTextField(
                                value = password,
                                onValueChange = { password = it },
                                label = { Text("Password") },
                                leadingIcon = {
                                    Icon(Icons.Default.Lock, contentDescription = null)
                                },
                                visualTransformation = PasswordVisualTransformation(),
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(20.dp))

                            Button(
                                onClick = {
                                    if (username.isNotBlank() && password.isNotBlank()) {
                                        onLoginSuccess()
                                    }
                                },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(54.dp),
                                shape = RoundedCornerShape(18.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = DeepForest)
                            ) {
                                Text("Login")
                            }

                            Spacer(modifier = Modifier.height(8.dp))

                            Text(
                                text = "Demo: enter any username and password",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color.Gray
                            )
                        }
                    }
                }
            }
        }

        @Composable
        fun SelectionScreen(
            onDairySelected: () -> Unit,
            onMaizeSelected: () -> Unit,
            onRecordsSelected: () -> Unit
        ) {
            AppBackground {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(22.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Spacer(modifier = Modifier.height(18.dp))

                    LogoImage(modifier = Modifier.size(160.dp))

                    Text(
                        text = "Welcome, Farmer",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.ExtraBold,
                        color = DeepForest
                    )

                    Text(
                        text = "Choose what you want to track today",
                        style = MaterialTheme.typography.bodyLarge,
                        color = FarmGreen,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    SelectionCard(
                        title = "Dairy",
                        description = "Salary, transport, tick spray, deworming and AI",
                        icon = Icons.Default.LocalDrink,
                        onClick = onDairySelected
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    SelectionCard(
                        title = "Maize",
                        description = "Fuel, driver salary, sprays, fertilizer and transport",
                        icon = Icons.Default.Agriculture,
                        onClick = onMaizeSelected
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Button(
                        onClick = onRecordsSelected,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(56.dp),
                        shape = RoundedCornerShape(18.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = FarmGreen)
                    ) {
                        Icon(Icons.Default.Calculate, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("View Submitted Records")
                    }
                }
            }
        }

        @OptIn(ExperimentalMaterial3Api::class)
        @Composable
        fun SelectionCard(
            title: String,
            description: String,
            icon: ImageVector,
            onClick: () -> Unit
        ) {
            Card(
                onClick = onClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(132.dp),
                shape = RoundedCornerShape(28.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 7.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(20.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(72.dp)
                            .background(SoftGreen, RoundedCornerShape(22.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = icon,
                            contentDescription = null,
                            tint = DeepForest,
                            modifier = Modifier.size(38.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(18.dp))

                    Column(
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(
                            text = title,
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.ExtraBold,
                            color = DeepForest
                        )

                        Spacer(modifier = Modifier.height(4.dp))

                        Text(
                            text = description,
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color(0xFF496B5B)
                        )
                    }
                }
            }
        }

        @Composable
        fun ExpenseFormScreen(
            title: String,
            subtitle: String,
            icon: ImageVector,
            fields: List<String>,
            submitButtonText: String,
            onBack: () -> Unit,
            onSubmit: (ExpenseRecord) -> Unit
        ) {
            val expenseValues = remember {
                mutableStateMapOf<String, String>().apply {
                    fields.forEach { put(it, "") }
                }
            }

            val total = expenseValues.values.sumOf {
                it.replace(",", "").trim().toDoubleOrNull() ?: 0.0
            }

            AppBackground {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(20.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(onClick = onBack) {
                            Icon(
                                imageVector = Icons.Default.ArrowBack,
                                contentDescription = "Back",
                                tint = DeepForest
                            )
                        }

                        Text(
                            text = title,
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.ExtraBold,
                            color = DeepForest
                        )
                    }

                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(28.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        elevation = CardDefaults.cardElevation(defaultElevation = 7.dp)
                    ) {
                        Column(
                            modifier = Modifier.padding(20.dp)
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(58.dp)
                                        .background(SoftGreen, RoundedCornerShape(18.dp)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(
                                        imageVector = icon,
                                        contentDescription = null,
                                        tint = DeepForest,
                                        modifier = Modifier.size(32.dp)
                                    )
                                }

                                Spacer(modifier = Modifier.width(14.dp))

                                Column {
                                    Text(
                                        text = title,
                                        style = MaterialTheme.typography.titleMedium,
                                        fontWeight = FontWeight.Bold,
                                        color = DeepForest
                                    )

                                    Text(
                                        text = subtitle,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = Color.Gray
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(20.dp))

                            fields.forEach { field ->
                                OutlinedTextField(
                                    value = expenseValues[field] ?: "",
                                    onValueChange = { value ->
                                        val cleaned = value.filter { it.isDigit() || it == '.' || it == ',' }
                                        expenseValues[field] = cleaned
                                    },
                                    label = { Text(field + " - KES") },
                                    prefix = { Text("KSh ") },
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    singleLine = true,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 6.dp)
                                )
                            }

                            Spacer(modifier = Modifier.height(14.dp))

                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(20.dp),
                                colors = CardDefaults.cardColors(containerColor = SoftGreen)
                            ) {
                                Column(
                                    modifier = Modifier.padding(18.dp)
                                ) {
                                    Text(
                                        text = "Total Expenses",
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = Color(0xFF496B5B)
                                    )

                                    Text(
                                        text = formatKes(total),
                                        style = MaterialTheme.typography.headlineSmall,
                                        fontWeight = FontWeight.ExtraBold,
                                        color = DeepForest
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(20.dp))

                            Button(
                                onClick = {
                                    val record = ExpenseRecord(
                                        category = title.removeSuffix(" Expenses"),
                                        total = total,
                                        date = currentDate(),
                                        items = expenseValues.toMap()
                                    )
                                    onSubmit(record)
                                },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(56.dp),
                                shape = RoundedCornerShape(18.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = DeepForest)
                            ) {
                                Text(submitButtonText)
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(30.dp))
                }
            }
        }

        @Composable
        fun RecordsScreen(records: List<ExpenseRecord>, onBack: () -> Unit) {
            AppBackground {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(20.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(onClick = onBack) {
                            Icon(
                                imageVector = Icons.Default.ArrowBack,
                                contentDescription = "Back",
                                tint = DeepForest
                            )
                        }

                        Text(
                            text = "Submitted Records",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.ExtraBold,
                            color = DeepForest
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    if (records.isEmpty()) {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(24.dp),
                            colors = CardDefaults.cardColors(containerColor = Color.White)
                        ) {
                            Column(
                                modifier = Modifier.padding(22.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text(
                                    text = "No records yet",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = DeepForest
                                )
                                Text(
                                    text = "Submit a Dairy or Maize expense record first.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = Color.Gray,
                                    textAlign = TextAlign.Center
                                )
                            }
                        }
                    } else {
                        records.forEach { record ->
                            RecordCard(record = record)
                            Spacer(modifier = Modifier.height(14.dp))
                        }
                    }
                }
            }
        }

        @Composable
        fun RecordCard(record: ExpenseRecord) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 5.dp)
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = record.category,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.ExtraBold,
                                color = DeepForest
                            )
                            Text(
                                text = record.date,
                                style = MaterialTheme.typography.bodySmall,
                                color = Color.Gray
                            )
                        }

                        Text(
                            text = formatKes(record.total),
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.ExtraBold,
                            color = FarmGreen
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))
                    HorizontalDivider()
                    Spacer(modifier = Modifier.height(10.dp))

                    record.items.filter { it.value.isNotBlank() }.forEach { item ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 3.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = item.key,
                                style = MaterialTheme.typography.bodyMedium,
                                color = Color(0xFF496B5B)
                            )

                            Text(
                                text = "KSh " + item.value,
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = DeepForest
                            )
                        }
                    }
                }
            }
        }

        fun currentDate(): String {
            val formatter = SimpleDateFormat("dd MMM yyyy, HH:mm", Locale.getDefault())
            return formatter.format(Date())
        }

        fun formatKes(amount: Double): String {
            val formatter = NumberFormat.getNumberInstance(Locale.US)
            formatter.minimumFractionDigits = 2
            formatter.maximumFractionDigits = 2
            return "KSh " + formatter.format(amount)
        }
    """)


def create_readme() -> None:
    write_file(PROJECT_DIR / "README.md", """
        # Pesa Za Shamba Android App

        This Android Studio project was generated by `pesaZaShambaApp.py`.

        ## App screens

        1. Login screen
        2. Dairy/Maize selection screen
        3. Dairy expense form
        4. Maize expense form
        5. Submitted records screen

        ## Logo

        The script copies the logo from:

        `C:\\Users\\kirwa\\Documents\\coding\\codeScripts\\peza_za_shamba_logo.png`

        into:

        `app/src/main/res/drawable/pesa_za_shamba_logo.png`

        ## Open in Android Studio

        Open this folder:

        `C:\\Users\\kirwa\\AndroidStudioProjects\\PesaZaShambaApp`

        Let Gradle sync, then click Run.

        ## Note

        Records are saved temporarily in memory for this first version. When the app is closed, records disappear.

        The next upgrade should use Room Database or Firebase so expenses are permanently saved.
    """)


def main() -> None:
    print("Creating Pesa Za Shamba Android Studio project...")
    print(f"Project folder: {PROJECT_DIR}")

    create_project_structure()
    copy_logo()
    create_gradle_files()
    create_android_manifest()
    create_resource_files()
    create_main_activity()
    create_readme()

    print("\n[SUCCESS] Android project created.")
    print(f"Open this folder in Android Studio:\n{PROJECT_DIR}")
    print("\nThen wait for Gradle Sync to finish and press Run.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n[ERROR] Project generation failed.")
        print(error)
        sys.exit(1)
