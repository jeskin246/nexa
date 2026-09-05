package com.nexa.nexa_app

import android.app.AlarmManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.app.NotificationManagerCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : FlutterActivity() {

    companion object {
        private const val METHOD_CHANNEL = "com.nexa.nexa_app/notification_listener"
        private const val EVENT_CHANNEL = "com.nexa.nexa_app/notification_events"
        private const val AUTOMATION_METHOD_CHANNEL = "com.nexa.nexa_app/automation"
        private const val AUTOMATION_EVENT_CHANNEL = "com.nexa.nexa_app/automation_events"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val permissionsNeeded = mutableListOf<String>()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            permissionsNeeded.add(Manifest.permission.READ_CONTACTS)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            permissionsNeeded.add(Manifest.permission.RECORD_AUDIO)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                permissionsNeeded.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        if (permissionsNeeded.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, permissionsNeeded.toTypedArray(), 1001)
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        flutterEngine.plugins.add(ScheduledWhatsAppPlugin())

        NexaDeviceStateManager.init(this)
        NexaForegroundService.startService(this)

        // 1. Auto-Reply NotificationListener Channel
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, METHOD_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "isNotificationPermissionGranted" -> {
                    val packageName = packageName
                    val enabledPackages = NotificationManagerCompat.getEnabledListenerPackages(this)
                    val isGranted = enabledPackages.contains(packageName)
                    result.success(isGranted)
                }
                "openNotificationPermissionSettings" -> {
                    val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    startActivity(intent)
                    result.success(true)
                }
                "sendDirectReply" -> {
                    val key = call.argument<String>("notificationKey") ?: ""
                    val replyText = call.argument<String>("replyText") ?: ""

                    if (key.isEmpty() || replyText.isEmpty()) {
                        result.error("INVALID_ARGS", "Notification key or reply text missing", null)
                        return@setMethodCallHandler
                    }

                    val success = NexoNotificationListener.sendDirectReply(this, key, replyText)
                    result.success(success)
                }
                else -> result.notImplemented()
            }
        }

        EventChannel(flutterEngine.dartExecutor.binaryMessenger, EVENT_CHANNEL).setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    NexoNotificationListener.eventSink = events
                }

                override fun onCancel(arguments: Any?) {
                    NexoNotificationListener.eventSink = null
                }
            }
        )

        // 2. System-Level Automation Channel
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, AUTOMATION_METHOD_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "getDeviceState" -> {
                    result.success(NexaDeviceStateManager.getDeviceStateSummary(this))
                }
                "getAuthStatus" -> {
                    result.success(NexaSecureAuthManager.getAuthStatusMap(this))
                }
                "scheduleTask" -> {
                    val taskId = call.argument<String>("taskId") ?: ""
                    val executionId = call.argument<String>("executionId") ?: ""
                    val recipient = call.argument<String>("recipient") ?: ""
                    val message = call.argument<String>("message") ?: ""
                    val timestampObj = call.argument<Any>("timestamp")
                    val timestamp: Long = when (timestampObj) {
                        is Long -> timestampObj
                        is Int -> timestampObj.toLong()
                        is Number -> timestampObj.toLong()
                        is String -> timestampObj.toLongOrNull() ?: 0L
                        else -> 0L
                    }

                    val ok = NexaTaskService.scheduleTaskAlarm(
                        context = this,
                        taskId = taskId,
                        executionId = executionId,
                        recipient = recipient,
                        message = message,
                        timestamp = timestamp
                    )
                    result.success(ok)
                }
                "cancelTask" -> {
                    val taskId = call.argument<String>("taskId") ?: ""
                    NexaTaskService.cancelTaskAlarm(this, taskId)
                    result.success(true)
                }
                "openAutostartSettings" -> {
                    val intent = Intent()
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    try {
                        intent.setClassName("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity")
                        startActivity(intent)
                    } catch (_: Exception) {
                        try {
                            intent.action = Settings.ACTION_APPLICATION_DETAILS_SETTINGS
                            intent.data = Uri.fromParts("package", packageName, null)
                            startActivity(intent)
                        } catch (_: Exception) {}
                    }
                    result.success(true)
                }
                "openBatteryOptimizationSettings" -> {
                    val intent = Intent()
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    try {
                        intent.action = Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS
                        startActivity(intent)
                    } catch (_: Exception) {
                        try {
                            intent.action = Settings.ACTION_APPLICATION_DETAILS_SETTINGS
                            intent.data = Uri.fromParts("package", packageName, null)
                            startActivity(intent)
                        } catch (_: Exception) {}
                    }
                    result.success(true)
                }
                "canScheduleExactAlarms" -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        val alarmManager = getSystemService(Context.ALARM_SERVICE) as AlarmManager
                        result.success(alarmManager.canScheduleExactAlarms())
                    } else {
                        result.success(true)
                    }
                }
                "openExactAlarmSettings" -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        val intent = Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM).apply {
                            data = Uri.fromParts("package", packageName, null)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        startActivity(intent)
                    }
                    result.success(true)
                }
                "openAccessibilitySettings" -> {
                    NexoGestureUnlockService.openAccessibilitySettings(this)
                    result.success(true)
                }
                "openAppDetailsSettings" -> {
                    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                        data = Uri.fromParts("package", packageName, null)
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    startActivity(intent)
                    result.success(true)
                }
                "openDisplayOverOtherAppsSettings" -> {
                    val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION).apply {
                        data = Uri.fromParts("package", packageName, null)
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    try {
                        startActivity(intent)
                    } catch (_: Exception) {
                        val appIntent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                            data = Uri.fromParts("package", packageName, null)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        startActivity(appIntent)
                    }
                    result.success(true)
                }
                "openMiuiPermissionEditor" -> {
                    val intent = Intent("miui.intent.action.APP_PERM_EDITOR").apply {
                        setClassName("com.miui.securitycenter", "com.miui.permcenter.permissions.PermissionsEditorActivity")
                        putExtra("extra_pkgname", packageName)
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    try {
                        startActivity(intent)
                    } catch (_: Exception) {
                        val appIntent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                            data = Uri.fromParts("package", packageName, null)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        startActivity(appIntent)
                    }
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }

        EventChannel(flutterEngine.dartExecutor.binaryMessenger, AUTOMATION_EVENT_CHANNEL).setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    NexaTaskService.automationEventSink = events
                }

                override fun onCancel(arguments: Any?) {
                    NexaTaskService.automationEventSink = null
                }
            }
        )
    }
}
