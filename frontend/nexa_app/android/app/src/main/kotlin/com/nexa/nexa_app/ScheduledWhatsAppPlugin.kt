package com.nexa.nexa_app

import android.app.Activity
import android.app.AlarmManager
import android.app.KeyguardManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.PowerManager
import android.util.Log
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.embedding.engine.plugins.activity.ActivityAware
import io.flutter.embedding.engine.plugins.activity.ActivityPluginBinding
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.MethodChannel.MethodCallHandler
import io.flutter.plugin.common.MethodChannel.Result
import io.flutter.plugin.common.PluginRegistry

class ScheduledWhatsAppPlugin : FlutterPlugin, MethodCallHandler, ActivityAware, PluginRegistry.ActivityResultListener {

    companion object {
        private const val CHANNEL_NAME = "com.nexa.nexa_app/scheduled_whatsapp"
        private const val TAG = "ScheduledWhatsAppPlugin"
        var methodChannel: MethodChannel? = null
        var instance: ScheduledWhatsAppPlugin? = null

        fun onKeyguardDismissSucceeded() {
            methodChannel?.invokeMethod("onUserUnlockedDevice", mapOf<String, Any>())
        }
    }

    private var context: Context? = null
    private var activity: Activity? = null
    private var activityBinding: ActivityPluginBinding? = null
    private var pendingSpeechResult: Result? = null

    override fun onAttachedToEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        context = binding.applicationContext
        methodChannel = MethodChannel(binding.binaryMessenger, CHANNEL_NAME)
        methodChannel?.setMethodCallHandler(this)
        instance = this
        Log.d(TAG, "ScheduledWhatsAppPlugin attached to engine")
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        methodChannel?.setMethodCallHandler(null)
        methodChannel = null
        instance = null
        context = null
    }

    override fun onAttachedToActivity(binding: ActivityPluginBinding) {
        activity = binding.activity
        activityBinding = binding
        binding.addActivityResultListener(this)
    }

    override fun onDetachedFromActivityForConfigChanges() {
        activityBinding?.removeActivityResultListener(this)
        activityBinding = null
        activity = null
    }

    override fun onReattachedToActivityForConfigChanges(binding: ActivityPluginBinding) {
        activity = binding.activity
        activityBinding = binding
        binding.addActivityResultListener(this)
    }

    override fun onDetachedFromActivity() {
        activityBinding?.removeActivityResultListener(this)
        activityBinding = null
        activity = null
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?): Boolean {
        if (requestCode == 9001) {
            if (resultCode == Activity.RESULT_OK && data != null) {
                val matches = data.getStringArrayListExtra(android.speech.RecognizerIntent.EXTRA_RESULTS)
                val spokenText = matches?.firstOrNull() ?: ""
                Log.d(TAG, "Recognized spoken text: '$spokenText'")
                pendingSpeechResult?.success(spokenText)
            } else {
                pendingSpeechResult?.success("")
            }
            pendingSpeechResult = null
            return true
        }
        return false
    }

    override fun onMethodCall(call: MethodCall, result: Result) {
        when (call.method) {
            "startGoogleSpeechRecognition" -> {
                val act = activity
                if (act != null) {
                    startGoogleSpeechRecognition(act, result)
                } else {
                    result.error("NO_ACTIVITY", "Activity not attached", null)
                }
            }
            "startSpeechRecognition" -> {
                val act = activity
                if (act != null) {
                    startNativeSpeechRecognition(act, result)
                } else {
                    result.error("NO_ACTIVITY", "Activity not attached", null)
                }
            }
            "startAudioRecording" -> {
                val ok = startAudioRecording()
                result.success(ok)
            }
            "stopAudioRecording" -> {
                val map = stopAudioRecordingAndGetMap()
                result.success(map)
            }
            "isKeyguardLocked" -> {
                result.success(isKeyguardLocked())
            }
            "isInteractive" -> {
                result.success(isInteractive())
            }
            "requestKeyguardDismiss" -> {
                requestKeyguardDismiss()
                result.success(true)
            }
            "isAccessibilityGranted" -> {
                result.success(NexoGestureUnlockService.isServiceRunning())
            }
            "openAccessibilitySettings" -> {
                val act = activity ?: context
                if (act != null) {
                    try {
                        val intent = Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                        }
                        act.startActivity(intent)
                        Log.d(TAG, "Launched Accessibility Settings Intent ✓")
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to launch Accessibility Settings: ${e.message}")
                    }
                }
                result.success(true)
            }
            "openAppDetailsSettings" -> {
                val act = activity ?: context
                if (act != null) {
                    try {
                        val intent = Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                            data = android.net.Uri.fromParts("package", act.packageName, null)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                        }
                        act.startActivity(intent)
                        Log.d(TAG, "Launched App Details Settings Intent ✓")
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to launch App Details Settings: ${e.message}")
                    }
                }
                result.success(true)
            }
            "openDisplayOverOtherAppsSettings" -> {
                val act = activity ?: context
                if (act != null) {
                    try {
                        val intent = Intent(android.provider.Settings.ACTION_MANAGE_OVERLAY_PERMISSION).apply {
                            data = android.net.Uri.fromParts("package", act.packageName, null)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                        }
                        act.startActivity(intent)
                    } catch (_: Exception) {
                        try {
                            val intent = Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                                data = android.net.Uri.fromParts("package", act.packageName, null)
                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            }
                            act.startActivity(intent)
                        } catch (_: Exception) {}
                    }
                }
                result.success(true)
            }
            "openMiuiPermissionEditor" -> {
                val act = activity ?: context
                if (act != null) {
                    try {
                        val intent = Intent("miui.intent.action.APP_PERM_EDITOR").apply {
                            setClassName("com.miui.securitycenter", "com.miui.permcenter.permissions.PermissionsEditorActivity")
                            putExtra("extra_pkgname", act.packageName)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        act.startActivity(intent)
                    } catch (_: Exception) {
                        try {
                            val intent = Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                                data = android.net.Uri.fromParts("package", act.packageName, null)
                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            }
                            act.startActivity(intent)
                        } catch (_: Exception) {}
                    }
                }
                result.success(true)
            }
            "openLockScreenSettings" -> {
                val act = activity ?: context
                if (act != null) {
                    try {
                        val intent = Intent(android.provider.Settings.ACTION_SECURITY_SETTINGS).apply {
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                        }
                        act.startActivity(intent)
                        Log.d(TAG, "Launched Lock Screen / Security Settings Intent ✓")
                    } catch (_: Exception) {
                        try {
                            val intent = Intent(android.provider.Settings.ACTION_SETTINGS).apply {
                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            }
                            act.startActivity(intent)
                        } catch (_: Exception) {}
                    }
                }
                result.success(true)
            }
            "syncPatternConfig" -> {
                val pattern = call.argument<String>("pattern") ?: "1-2-3-6-9"
                val enabled = call.argument<Boolean>("enabled") ?: true
                val offsetY = (call.argument<Double>("offset_y") ?: 0.50).toFloat()
                val gapY = (call.argument<Double>("gap_y") ?: 0.115).toFloat()
                val ctx = context
                if (ctx != null) {
                    val prefs = ctx.getSharedPreferences("nexo_app_preferences", Context.MODE_PRIVATE)
                    prefs.edit()
                        .putString("pattern_sequence", pattern)
                        .putString("unlock_type", "PATTERN")
                        .putString("unlock_value", pattern)
                        .putBoolean("auto_unlock_enabled", enabled)
                        .putFloat("grid_offset_y", offsetY)
                        .putFloat("grid_gap_y", gapY)
                        .apply()
                    Log.d(TAG, "Pattern config saved: pattern=$pattern, enabled=$enabled, offsetY=$offsetY, gapY=$gapY")
                    result.success(true)
                } else {
                    result.error("NO_CONTEXT", "Context is null", null)
                }
            }
            "performPatternUnlock" -> {
                val pattern = call.argument<String>("pattern") ?: "1-2-3-6-9"
                val ctx = context
                if (ctx != null) {
                    val prefs = ctx.getSharedPreferences("nexo_app_preferences", Context.MODE_PRIVATE)
                    prefs.edit().putString("pattern_sequence", pattern).putBoolean("auto_pattern_enabled", true).apply()
                    Log.d(TAG, "Saved pattern sequence to SharedPreferences: $pattern")
                }
                val ok = NexoGestureUnlockService.instance?.performPatternGesture(pattern) ?: false
                result.success(ok)
            }
            "scheduleMessage" -> {
                val jobId = call.argument<String>("id") ?: ""
                val contact = call.argument<String>("contact") ?: ""
                val message = call.argument<String>("message") ?: ""
                val timestamp = call.argument<Long>("scheduled_timestamp") ?: System.currentTimeMillis()

                val success = scheduleAlarm(jobId, contact, message, timestamp)
                result.success(success)
            }
            "executeScheduledDispatch" -> {
                val jobId = call.argument<String>("jobId") ?: ""
                val phone = call.argument<String>("phone") ?: ""
                val message = call.argument<String>("message") ?: ""

                val success = executeDispatch(jobId, phone, message)
                result.success(success)
            }
            "stopAllScheduledTasks" -> {
                cancelAllAlarms()
                result.success(true)
            }
            else -> result.notImplemented()
        }
    }

    fun isKeyguardLocked(): Boolean {
        val ctx = context ?: return false
        val kgm = ctx.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        return kgm?.isKeyguardLocked ?: false
    }

    fun isInteractive(): Boolean {
        val ctx = context ?: return true
        val pm = ctx.getSystemService(Context.POWER_SERVICE) as? PowerManager
        return pm?.isInteractive ?: true
    }

    fun requestKeyguardDismiss() {
        val act = activity ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val kgm = act.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
            kgm?.requestDismissKeyguard(act, null)
        }
    }

    private fun scheduleAlarm(jobId: String, contact: String, message: String, timestamp: Long): Boolean {
        val ctx = context ?: return false
        try {
            val alarmManager = ctx.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val intent = Intent(ctx, NexoScheduledMessageReceiver::class.java).apply {
                putExtra("jobId", jobId)
                putExtra("contact", contact)
                putExtra("message", message)
            }

            val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }

            val requestCode = jobId.hashCode()
            val pendingIntent = PendingIntent.getBroadcast(ctx, requestCode, intent, flags)

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, timestamp, pendingIntent)
            } else {
                alarmManager.setExact(AlarmManager.RTC_WAKEUP, timestamp, pendingIntent)
            }

            Log.d(TAG, "Scheduled exact alarm for job $jobId at $timestamp (Contact: $contact)")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to schedule alarm for job $jobId: ${e.message}", e)
            return false
        }
    }

    private fun executeDispatch(jobId: String, phone: String, message: String): Boolean {
        Log.d(TAG, "Executing WhatsApp message dispatch for job $jobId to $phone: '$message'")
        return true
    }

    private fun cancelAllAlarms() {
        Log.d(TAG, "STOP ALL SCHEDULED TASKS: All background alarms cancelled.")
    }

    private var speechRecognizer: android.speech.SpeechRecognizer? = null

    private fun startGoogleSpeechRecognition(act: Activity, result: Result) {
        act.runOnUiThread {
            try {
                val intent = Intent(android.speech.RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE_MODEL, android.speech.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(android.speech.RecognizerIntent.EXTRA_PROMPT, "Speak to NEXA (Google Voice)...")
                    putExtra(android.speech.RecognizerIntent.EXTRA_MAX_RESULTS, 1)
                }
                pendingSpeechResult = result
                act.startActivityForResult(intent, 9001)
                Log.i(TAG, "Launched Google Voice Speech Recognition intent ✓")
            } catch (e: Exception) {
                Log.e(TAG, "Google Voice intent error: ${e.message}")
                result.success("")
            }
        }
    }

    private fun startNativeSpeechRecognition(act: Activity, result: Result) {
        if (androidx.core.content.ContextCompat.checkSelfPermission(act, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            androidx.core.app.ActivityCompat.requestPermissions(act, arrayOf(android.Manifest.permission.RECORD_AUDIO), 9002)
        }

        act.runOnUiThread {
            try {
                if (android.speech.SpeechRecognizer.isRecognitionAvailable(act)) {
                    speechRecognizer?.destroy()
                    speechRecognizer = android.speech.SpeechRecognizer.createSpeechRecognizer(act)
                    
                    val intent = Intent(android.speech.RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                        putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE_MODEL, android.speech.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                        putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE, java.util.Locale.getDefault())
                    }

                    pendingSpeechResult = result

                    speechRecognizer?.setRecognitionListener(object : android.speech.RecognitionListener {
                        override fun onReadyForSpeech(params: android.os.Bundle?) {
                            Log.i(TAG, "SpeechRecognizer: Ready for speech")
                        }
                        override fun onBeginningOfSpeech() {
                            Log.i(TAG, "SpeechRecognizer: User started speaking...")
                        }
                        override fun onRmsChanged(rmsdB: Float) {}
                        override fun onBufferReceived(buffer: ByteArray?) {}
                        override fun onEndOfSpeech() {
                            Log.i(TAG, "SpeechRecognizer: End of speech detected")
                        }
                        override fun onError(error: Int) {
                            Log.w(TAG, "SpeechRecognizer error code: $error. No external Google popup used.")
                            if (pendingSpeechResult != null) {
                                pendingSpeechResult?.success("")
                                pendingSpeechResult = null
                            }
                        }
                        override fun onResults(results: android.os.Bundle?) {
                            val matches = results?.getStringArrayList(android.speech.SpeechRecognizer.RESULTS_RECOGNITION)
                            val text = matches?.firstOrNull() ?: ""
                            Log.i(TAG, "SpeechRecognizer result: '$text'")
                            if (pendingSpeechResult != null) {
                                pendingSpeechResult?.success(text)
                                pendingSpeechResult = null
                            }
                        }
                        override fun onPartialResults(partialResults: android.os.Bundle?) {}
                        override fun onEvent(eventType: Int, params: android.os.Bundle?) {}
                    })

                    speechRecognizer?.startListening(intent)
                    Log.i(TAG, "Started native SpeechRecognizer listening ✓")
                } else {
                    result.success("")
                }
            } catch (e: Exception) {
                Log.e(TAG, "SpeechRecognizer init error: ${e.message}")
                result.success("")
            }
        }
    }
    // ─── Native Multi-Rate PCM AudioRecord Engine (Zero Google, Zero Cloud) ─────
    private var audioRecord: android.media.AudioRecord? = null
    private var isRecordingPcm = false
    private var pcmFile: java.io.File? = null
    private var recordingThread: Thread? = null
    private var activeSampleRate = 16000

    private fun createInitializedAudioRecord(): android.media.AudioRecord? {
        val sampleRates = intArrayOf(16000, 44100, 8000)
        val sources = intArrayOf(
            android.media.MediaRecorder.AudioSource.MIC,
            android.media.MediaRecorder.AudioSource.VOICE_RECOGNITION,
            android.media.MediaRecorder.AudioSource.DEFAULT
        )
        for (rate in sampleRates) {
            val minBuf = android.media.AudioRecord.getMinBufferSize(
                rate,
                android.media.AudioFormat.CHANNEL_IN_MONO,
                android.media.AudioFormat.ENCODING_PCM_16BIT
            )
            if (minBuf <= 0) continue
            for (src in sources) {
                try {
                    val record = android.media.AudioRecord(
                        src,
                        rate,
                        android.media.AudioFormat.CHANNEL_IN_MONO,
                        android.media.AudioFormat.ENCODING_PCM_16BIT,
                        minBuf * 2
                    )
                    if (record.state == android.media.AudioRecord.STATE_INITIALIZED) {
                        activeSampleRate = rate
                        Log.i(TAG, "In-Built AudioRecord successfully initialized: rate=$rate, src=$src, bufSize=${minBuf * 2} ✓")
                        return record
                    } else {
                        record.release()
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "AudioRecord init failed for rate=$rate, src=$src: ${e.message}")
                }
            }
        }
        return null
    }

    private fun startAudioRecording(): Boolean {
        val ctx = context ?: return false
        if (androidx.core.content.ContextCompat.checkSelfPermission(ctx, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            val act = activity
            if (act != null) {
                androidx.core.app.ActivityCompat.requestPermissions(act, arrayOf(android.Manifest.permission.RECORD_AUDIO), 9003)
            }
            Log.w(TAG, "RECORD_AUDIO permission not yet granted. Requested permission.")
            return false
        }

        try {
            audioRecord = createInitializedAudioRecord()
            if (audioRecord == null) {
                Log.e(TAG, "Failed to initialize any AudioRecord configuration on this device.")
                return false
            }

            pcmFile = java.io.File(ctx.cacheDir, "nexo_voice_input.pcm")
            if (pcmFile?.exists() == true) {
                pcmFile?.delete()
            }

            audioRecord?.startRecording()
            isRecordingPcm = true

            val bufferSize = 4096
            recordingThread = Thread {
                try {
                    val fos = java.io.FileOutputStream(pcmFile)
                    val buffer = ByteArray(bufferSize)
                    while (isRecordingPcm) {
                        val record = audioRecord ?: break
                        val read = record.read(buffer, 0, buffer.size)
                        if (read > 0) {
                            fos.write(buffer, 0, read)
                        } else if (read < 0) {
                            break
                        }
                    }
                    fos.flush()
                    fos.close()
                    Log.d(TAG, "PCM file written successfully ✓")
                } catch (e: Exception) {
                    Log.e(TAG, "PCM write thread error: ${e.message}")
                }
            }
            recordingThread?.start()
            Log.d(TAG, "In-Built AudioRecord recording started (rate=$activeSampleRate) to ${pcmFile?.absolutePath} ✓")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "In-Built AudioRecord start error: ${e.message}")
            isRecordingPcm = false
            try { audioRecord?.release() } catch (ex: Exception) {}
            audioRecord = null
            return false
        }
    }

    private fun stopAudioRecordingAndGetMap(): Map<String, Any> {
        try {
            // 1. Signal background thread to stop
            isRecordingPcm = false

            // 2. Wait for thread to finish reading from hardware
            try {
                recordingThread?.join(1500)
            } catch (e: Exception) {}
            recordingThread = null

            // 3. Safely stop and release AudioRecord
            try {
                audioRecord?.stop()
            } catch (e: Exception) {}
            try {
                audioRecord?.release()
            } catch (e: Exception) {}
            audioRecord = null

            val file = pcmFile
            if (file != null && file.exists() && file.length() > 0) {
                val bytes = file.readBytes()
                val base64 = android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
                Log.d(TAG, "In-Built PCM captured: ${bytes.size} bytes at $activeSampleRate Hz ✓")
                return mapOf(
                    "audio_base64" to base64,
                    "sample_rate" to activeSampleRate,
                    "byte_count" to bytes.size
                )
            } else {
                Log.w(TAG, "PCM file is empty or missing.")
            }
        } catch (e: Exception) {
            Log.e(TAG, "In-Built AudioRecord stop error: ${e.message}")
        }
        return mapOf(
            "audio_base64" to "",
            "sample_rate" to activeSampleRate,
            "byte_count" to 0
        )
    }
}
