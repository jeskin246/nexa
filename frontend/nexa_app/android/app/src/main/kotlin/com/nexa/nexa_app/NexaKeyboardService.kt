package com.nexa.nexa_app

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.inputmethodservice.InputMethodService
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.widget.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class NexaKeyboardService : InputMethodService() {

    companion object {
        private const val TAG = "NexaKeyboardService"
        private val executor = Executors.newSingleThreadExecutor()
    }

    private var activeTone = "professional"
    private var activeTargetLang = "tamil"
    private var isShifted = false
    private var isSymbolMode = false

    private val qwertyRows = arrayOf(
        arrayOf("q", "w", "e", "r", "t", "y", "u", "i", "o", "p"),
        arrayOf("a", "s", "d", "f", "g", "h", "j", "k", "l"),
        arrayOf("SHIFT", "z", "x", "c", "v", "b", "n", "m", "DEL"),
        arrayOf("?123", "🌐", "SPACE", ".", "ENTER")
    )

    private val symbolRows = arrayOf(
        arrayOf("1", "2", "3", "4", "5", "6", "7", "8", "9", "0"),
        arrayOf("@", "#", "$", "%", "&", "-", "+", "(", ")", "/"),
        arrayOf("ABC", "*", "\"", "'", ":", ";", "!", "?", "DEL"),
        arrayOf("ABC", "🌐", "SPACE", ",", "ENTER")
    )

    override fun onCreateInputView(): View {
        val rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0D111A"))
            setPadding(8, 8, 8, 16)
        }

        // 1. AI Enhancement Toolbar
        val aiBar = createAiToolbar()
        rootLayout.addView(aiBar)

        // 2. Main Keypad Container
        val keypadContainer = LinearLayout(this).apply {
            id = View.generateViewId()
            orientation = LinearLayout.VERTICAL
        }
        renderKeypad(keypadContainer)
        rootLayout.addView(keypadContainer)

        return rootLayout
    }

    private fun createAiToolbar(): View {
        val scroll = HorizontalScrollView(this).apply {
            isHorizontalScrollBarEnabled = false
            setPadding(0, 4, 0, 8)
        }

        val bar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }

        // NEXA Orb Badge
        val badge = TextView(this).apply {
            text = "NEXA AI"
            setTextColor(Color.parseColor("#00F2FE"))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
            setPadding(16, 8, 16, 8)
            background = GradientDrawable().apply {
                setColor(Color.parseColor("#15202B"))
                cornerRadius = 20f
                setStroke(2, Color.parseColor("#00F2FE"))
            }
        }
        bar.addView(badge)
        addDivider(bar)

        val chips = listOf(
            Triple("✨ Fix Grammar", "grammar_fix", null),
            Triple("👔 Professional", "professional", null),
            Triple("😊 Friendly", "friendly", null),
            Triple("⚡ Concise", "concise", null),
            Triple("🗣️ Casual", "casual", null),
            Triple("🇮🇳 Tamil", "translate", "tamil"),
            Triple("🇮🇳 Hindi", "translate", "hindi"),
            Triple("🇪🇸 Spanish", "translate", "spanish"),
            Triple("🇫🇷 French", "translate", "french"),
            Triple("🇩🇪 German", "translate", "german")
        )

        for ((label, tone, lang) in chips) {
            val chip = Button(this).apply {
                text = label
                setTextColor(Color.WHITE)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
                isAllCaps = false
                setPadding(20, 4, 20, 4)
                background = GradientDrawable().apply {
                    setColor(Color.parseColor("#1A2333"))
                    cornerRadius = 16f
                    setStroke(1, Color.parseColor("#2A3A50"))
                }
                setOnClickListener {
                    enhanceCurrentText(tone, lang)
                }
            }
            bar.addView(chip)
            addDivider(bar)
        }

        scroll.addView(bar)
        return scroll
    }

    private fun addDivider(parent: LinearLayout) {
        val space = View(this).apply {
            layoutParams = LinearLayout.LayoutParams(12, 1)
        }
        parent.addView(space)
    }

    private fun renderKeypad(container: LinearLayout) {
        container.removeAllViews()
        val rows = if (isSymbolMode) symbolRows else qwertyRows

        for (row in rows) {
            val rowLayout = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                gravity = Gravity.CENTER
                setPadding(0, 4, 0, 4)
            }

            for (key in row) {
                val btn = Button(this).apply {
                    val displayKey = when (key) {
                        "SHIFT" -> if (isShifted) "⬆️" else "⇧"
                        "DEL" -> "⌫"
                        "SPACE" -> "space"
                        "ENTER" -> "↵"
                        "?123" -> "?123"
                        "ABC" -> "ABC"
                        "🌐" -> "🌐"
                        else -> if (isShifted) key.uppercase() else key.lowercase()
                    }
                    text = displayKey
                    setTextColor(Color.WHITE)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, if (key == "SPACE") 13f else 16f)
                    isAllCaps = false

                    val weight = when (key) {
                        "SPACE" -> 4.0f
                        "SHIFT", "DEL", "?123", "ABC", "ENTER" -> 1.5f
                        else -> 1.0f
                    }

                    layoutParams = LinearLayout.LayoutParams(0, 120, weight).apply {
                        setMargins(3, 3, 3, 3)
                    }

                    background = GradientDrawable().apply {
                        val isSpecial = key in listOf("SHIFT", "DEL", "?123", "ABC", "ENTER", "🌐")
                        setColor(if (isSpecial) Color.parseColor("#1F2937") else Color.parseColor("#151D28"))
                        cornerRadius = 12f
                        if (key == "ENTER") setStroke(2, Color.parseColor("#00F2FE"))
                    }

                    setOnClickListener {
                        handleKeyPress(key, container)
                    }
                }
                rowLayout.addView(btn)
            }
            container.addView(rowLayout)
        }
    }

    private fun handleKeyPress(key: String, container: LinearLayout) {
        val ic: InputConnection = currentInputConnection ?: return

        when (key) {
            "SHIFT" -> {
                isShifted = !isShifted
                renderKeypad(container)
            }
            "DEL" -> {
                ic.deleteSurroundingText(1, 0)
            }
            "SPACE" -> {
                ic.commitText(" ", 1)
            }
            "ENTER" -> {
                ic.sendKeyEvent(android.view.KeyEvent(android.view.KeyEvent.ACTION_DOWN, android.view.KeyEvent.KEYCODE_ENTER))
                ic.sendKeyEvent(android.view.KeyEvent(android.view.KeyEvent.ACTION_UP, android.view.KeyEvent.KEYCODE_ENTER))
            }
            "?123" -> {
                isSymbolMode = true
                renderKeypad(container)
            }
            "ABC" -> {
                isSymbolMode = false
                renderKeypad(container)
            }
            "🌐" -> {
                // Switch to next IME
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
                    switchToNextInputMethod(false)
                }
            }
            else -> {
                val charToCommit = if (isShifted) key.uppercase() else key.lowercase()
                ic.commitText(charToCommit, 1)
                if (isShifted) {
                    isShifted = false
                    renderKeypad(container)
                }
            }
        }
    }

    private fun enhanceCurrentText(tone: String, targetLang: String?) {
        val ic = currentInputConnection ?: return
        val before = ic.getTextBeforeCursor(1000, 0)?.toString() ?: ""
        val after = ic.getTextAfterCursor(1000, 0)?.toString() ?: ""
        val fullText = (before + after).trim()

        if (fullText.isEmpty()) {
            Toast.makeText(this, "Type a sentence first to enhance!", Toast.LENGTH_SHORT).show()
            return
        }

        Toast.makeText(this, "Enhancing with NEXA ($tone)...", Toast.LENGTH_SHORT).show()

        executor.execute {
            val enhanced = performEnhancement(fullText, tone, targetLang)
            Handler(Looper.getMainLooper()).post {
                val currentIc = currentInputConnection
                if (currentIc != null && enhanced.isNotEmpty()) {
                    // Select and replace all text
                    currentIc.deleteSurroundingText(before.length, after.length)
                    currentIc.commitText(enhanced, 1)
                    Toast.makeText(this, "Enhanced by NEXA ✓", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    fun performEnhancement(text: String, tone: String, targetLang: String?): String {
        try {
            val url = URL("https://nexa-backend-pqhw.onrender.com/api/ai/enhance-text")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.connectTimeout = 3000
            conn.readTimeout = 4000
            conn.doOutput = true

            val json = JSONObject().apply {
                put("text", text)
                put("tone", tone)
                if (targetLang != null) put("target_language", targetLang)
            }

            conn.outputStream.use { os ->
                os.write(json.toString().toByteArray(Charsets.UTF_8))
            }

            if (conn.responseCode == 200) {
                val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                val respJson = JSONObject(responseStr)
                return respJson.optString("enhanced_text", text)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Cloud AI enhancement fallback: ${e.message}")
        }

        // Fast Offline Fallback
        return localEnhanceFallback(text, tone, targetLang)
    }

    private fun localEnhanceFallback(text: String, tone: String, targetLang: String?): String {
        var res = text.trim()
        val replacements = mapOf(
            "\\bu\\b" to "you", "\\bur\\b" to "your", "\\bpls\\b" to "please",
            "\\bplz\\b" to "please", "\\bthx\\b" to "thanks", "\\btomm?or?r?ow\\b" to "tomorrow",
            "\\bmeting\\b" to "meeting", "\\bim\\b" to "I am", "\\bi\\b" to "I"
        )
        for ((k, v) in replacements) {
            res = res.replace(Regex("(?i)$k"), v)
        }
        if (res.isNotEmpty()) res = res[0].uppercase() + res.substring(1)

        return when (tone.lowercase()) {
            "professional" -> {
                res = res.replace(Regex("(?i)check docs"), "please review the documentation")
                    .replace(Regex("(?i)i will come"), "I will attend")
                if (!res.endsWith(".")) "$res." else res
            }
            "friendly" -> "Hey! ${res.trimEnd('.', '!', '?')} 😊"
            "concise" -> res.trimEnd('.', '!', '?') + "."
            "translate" -> if (targetLang?.lowercase() == "tamil") "வணக்கம்: $res" else "[$targetLang]: $res"
            else -> if (!res.endsWith(".")) "$res." else res
        }
    }
}
