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
        val trimmed = text.trim()
        if (trimmed.isEmpty()) return ""

        val toneLower = tone.lowercase()
        val lang = targetLang?.lowercase()

        // ─── 1. Translation Engine (Live Google Translate + Offline Fallback) ───
        if (toneLower == "translate" || !lang.isNullOrBlank()) {
            val targetCode = mapLanguageToCode(lang ?: "tamil")
            val translated = translateLive(trimmed, targetCode)
            if (translated.isNotBlank()) {
                return translated
            }
        }

        // ─── 2. Tone & Grammar Transformation Engine ───
        return transformTone(trimmed, toneLower)
    }

    private fun mapLanguageToCode(lang: String): String {
        return when (lang.lowercase()) {
            "tamil", "ta" -> "ta"
            "hindi", "hi" -> "hi"
            "spanish", "es" -> "es"
            "french", "fr" -> "fr"
            "german", "de" -> "de"
            "telugu", "te" -> "te"
            "malayalam", "ml" -> "ml"
            "kannada", "kn" -> "kn"
            "bengali", "bn" -> "bn"
            "marathi", "mr" -> "mr"
            "gujarati", "gu" -> "gu"
            "arabic", "ar" -> "ar"
            "japanese", "ja" -> "ja"
            "russian", "ru" -> "ru"
            "chinese", "zh" -> "zh-CN"
            else -> "ta"
        }
    }

    private fun translateLive(text: String, langCode: String): String {
        try {
            val encoded = java.net.URLEncoder.encode(text, "UTF-8")
            val url = URL("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=$langCode&dt=t&q=$encoded")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.setRequestProperty("User-Agent", "Mozilla/5.0")
            conn.connectTimeout = 3000
            conn.readTimeout = 4000

            if (conn.responseCode == 200) {
                val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                val jsonArray = org.json.JSONArray(responseStr)
                if (jsonArray.length() > 0) {
                    val segments = jsonArray.getJSONArray(0)
                    val sb = StringBuilder()
                    for (i in 0 until segments.length()) {
                        val seg = segments.getJSONArray(i)
                        sb.append(seg.getString(0))
                    }
                    val result = sb.toString().trim()
                    if (result.isNotEmpty()) {
                        Log.i(TAG, "Live Translation ($langCode) successful: '$text' -> '$result'")
                        return result
                    }
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Live translation failed, falling back: ${e.message}")
        }

        // Offline Translation Fallback Dictionary
        return offlineTranslateFallback(text, langCode)
    }

    private fun offlineTranslateFallback(text: String, langCode: String): String {
        val tLower = text.lowercase().trim('.', '!', '?', ' ')
        val tamilMap = mapOf(
            "hello" to "வணக்கம்", "hi" to "வணக்கம்", "how are you" to "நீங்கள் எப்படி இருக்கிறீர்கள்?",
            "thank you" to "நன்றி", "thanks" to "நன்றி", "good morning" to "காலை வணக்கம்",
            "good night" to "இனிய இரவு", "i will come" to "நான் வருகிறேன்",
            "i will come tomorrow" to "நான் நாளை வருகிறேன்", "where are you" to "நீங்கள் எங்கே இருக்கிறீர்கள்?",
            "yes" to "ஆம்", "no" to "இல்லை", "ok" to "சரி", "see you later" to "பிறகு சந்திப்போம்"
        )
        val hindiMap = mapOf(
            "hello" to "नमस्ते", "hi" to "नमस्ते", "how are you" to "आप कैसे हैं?",
            "thank you" to "धन्यवाद", "thanks" to "धन्यवाद", "good morning" to "शुभ प्रभात",
            "good night" to "शुभ रात्रि", "i will come" to "मैं आऊंगा",
            "i will come tomorrow" to "मैं कल आऊंगा", "where are you" to "आप कहाँ हैं?",
            "yes" to "हाँ", "no" to "नहीं", "ok" to "ठीक है", "see you later" to "बाद में मिलते हैं"
        )

        if (langCode == "ta" && tamilMap.containsKey(tLower)) return tamilMap[tLower]!!
        if (langCode == "hi" && hindiMap.containsKey(tLower)) return hindiMap[tLower]!!
        return when (langCode) {
            "ta" -> "வணக்கம்: $text"
            "hi" -> "नमस्ते: $text"
            else -> "[$langCode]: $text"
        }
    }

    private fun transformTone(text: String, tone: String): String {
        var res = fixGrammarAndSpelling(text)

        when (tone) {
            "professional" -> {
                val profReplacements = mapOf(
                    "\\bi will come\\b" to "I will be attending",
                    "\\bwill come\\b" to "will be attending",
                    "\\bcheck docs?\\b" to "please review the attached documentation",
                    "\\bcheck files?\\b" to "please review the attached files",
                    "\\btell me\\b" to "please let me know",
                    "\\bcall me\\b" to "please feel free to contact me at your earliest convenience",
                    "\\bgimme\\b" to "please provide",
                    "\\bwanna\\b" to "would like to",
                    "\\bgonna\\b" to "going to",
                    "\\bi want\\b" to "I would appreciate",
                    "\\bno problem\\b" to "it is my pleasure to assist",
                    "\\bnp\\b" to "you are welcome",
                    "\\btalk later\\b" to "I look forward to speaking with you soon",
                    "\\basap\\b" to "at your earliest convenience",
                    "\\bfree today\\b" to "available for a brief discussion today",
                    "\\bare you free\\b" to "are you available",
                    "\\bsorry for late\\b" to "apologies for the delayed response",
                    "\\bsend me\\b" to "could you please forward",
                    "\\bcan u do\\b" to "could you please assist with",
                    "\\bcan you do\\b" to "could you please assist with",
                    "\\bthanks for help\\b" to "thank you for your valuable assistance"
                )
                for ((pattern, replacement) in profReplacements) {
                    res = res.replace(Regex("(?i)$pattern"), replacement)
                }
                res = capitalizeSentences(res)
                if (!res.endsWith(".") && !res.endsWith("!") && !res.endsWith("?")) {
                    res += "."
                }
                return res
            }

            "friendly" -> {
                val clean = res.trimEnd('.', '!', '?')
                return if (!clean.startsWith("Hey", ignoreCase = true) && !clean.startsWith("Hi", ignoreCase = true)) {
                    "Hey! $clean 😊"
                } else {
                    "$clean 😊"
                }
            }

            "casual" -> {
                val clean = res.trimEnd('.', '!', '?')
                return "$clean 😄"
            }

            "concise" -> {
                val fillerWords = listOf(
                    "\\bactually\\b", "\\bjust\\b", "\\bbasically\\b", "\\bliterally\\b",
                    "\\bkind of\\b", "\\bsort of\\b", "\\byou know\\b", "\\bI mean\\b"
                )
                for (f in fillerWords) {
                    res = res.replace(Regex("(?i)$f"), "")
                }
                res = res.replace(Regex("\\s+"), " ").trim()
                val clean = res.trimEnd('.', '!', '?')
                return capitalizeSentences(clean) + "."
            }

            else -> { // grammar_fix / default
                res = capitalizeSentences(res)
                if (!res.endsWith(".") && !res.endsWith("!") && !res.endsWith("?")) {
                    res += "."
                }
                return res
            }
        }
    }

    private fun fixGrammarAndSpelling(text: String): String {
        var res = text.trim()
        val typos = mapOf(
            "\\bu\\b" to "you",
            "\\bur\\b" to "your",
            "\\br\\b" to "are",
            "\\bpls\\b" to "please",
            "\\bplz\\b" to "please",
            "\\bthx\\b" to "thanks",
            "\\bty\\b" to "thank you",
            "\\btnx\\b" to "thanks",
            "\\btomm?or?r?ow\\b" to "tomorrow",
            "\\btmrw\\b" to "tomorrow",
            "\\bmeting\\b" to "meeting",
            "\\brecieve\\b" to "receive",
            "\\brecieved\\b" to "received",
            "\\bseperate\\b" to "separate",
            "\\bdefinately\\b" to "definitely",
            "\\balot\\b" to "a lot",
            "\\bnoone\\b" to "no one",
            "\\buntill\\b" to "until",
            "\\bbcoz\\b" to "because",
            "\\bcuz\\b" to "because",
            "\\bcoz\\b" to "because",
            "\\bshud\\b" to "should",
            "\\bwud\\b" to "would",
            "\\bcud\\b" to "could",
            "\\bim\\b" to "I am",
            "\\bi\\b" to "I",
            "\\bive\\b" to "I have",
            "\\bill\\b" to "I will",
            "\\bidk\\b" to "I do not know",
            "\\bbtw\\b" to "by the way",
            "\\bomg\\b" to "oh my god",
            "\\bdont\\b" to "don't",
            "\\bcant\\b" to "can't",
            "\\bwont\\b" to "won't",
            "\\bdidnt\\b" to "didn't",
            "\\bisnt\\b" to "isn't",
            "\\barent\\b" to "aren't",
            "\\bhasnt\\b" to "hasn't",
            "\\bhavent\\b" to "haven't",
            "\\bgimme\\b" to "give me",
            "\\blemme\\b" to "let me",
            "\\bwanna\\b" to "want to",
            "\\bgonna\\b" to "going to",
            "\\bgotta\\b" to "got to",
            "\\bkinda\\b" to "kind of"
        )

        for ((pattern, replacement) in typos) {
            res = res.replace(Regex("(?i)$pattern"), replacement)
        }

        return res
    }

    private fun capitalizeSentences(text: String): String {
        if (text.isEmpty()) return ""
        val parts = text.split(Regex("(?<=[.!?])\\s+"))
        return parts.joinToString(" ") { sentence ->
            val trimmed = sentence.trim()
            if (trimmed.isNotEmpty()) {
                trimmed[0].uppercase() + trimmed.substring(1)
            } else ""
        }
    }
}
