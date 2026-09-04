package com.nexa.nexa_app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import android.util.Log
import io.flutter.plugin.common.EventChannel
import org.json.JSONArray
import org.json.JSONObject

object NexaTaskService {
    private const val TAG = "NexaTaskService"
    private const val LOG_TAG = "NEXA_SCHED"
    private const val PREFS_PENDING = "nexa_pending_unlock_prefs"
    private const val KEY_PENDING_TASKS = "pending_unlock_list"

    var automationEventSink: EventChannel.EventSink? = null

    // Track task states in memory (synced with Flutter layer & persisted)
    private val taskStateMap = HashMap<String, String>()
    private val completedExecutions = HashSet<String>()

    fun scheduleTaskAlarm(
        context: Context,
        taskId: String,
        executionId: String,
        recipient: String,
        message: String,
        timestamp: Long
    ): Boolean {
        taskStateMap[taskId] = "SCHEDULED"
        return NexaSchedulerManager.scheduleTaskAlarm(
            context, taskId, executionId, recipient, message, timestamp
        )
    }

    fun cancelTaskAlarm(context: Context, taskId: String) {
        taskStateMap[taskId] = "CANCELLED"
        removePendingTask(context, taskId)
        NexaSchedulerManager.cancelTaskAlarm(context, taskId)
    }

    fun processAlarmTrigger(
        context: Context,
        taskId: String,
        executionId: String,
        recipient: String,
        message: String
    ) {
        if (completedExecutions.contains(executionId)) {
            Log.w(TAG, "Duplicate execution blocked for executionId=$executionId")
            return
        }

        try {
            val intent = android.content.Intent(context, NexaTaskExecutionActivity::class.java).apply {
                putExtra("taskId", taskId)
                putExtra("executionId", executionId)
                putExtra("recipient", recipient)
                putExtra("message", message)
                addFlags(
                    android.content.Intent.FLAG_ACTIVITY_NEW_TASK or
                    android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP or
                    android.content.Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                )
            }
            context.startActivity(intent)
            Log.i(TAG, "Started NexaTaskExecutionActivity over keyguard for taskId=$taskId ✓")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to launch NexaTaskExecutionActivity: ${e.message}. Fallback to direct automation engine...")
            NexaAutomationEngine.processScheduledTask(
                context = context,
                taskId = taskId,
                executionId = executionId,
                recipient = recipient,
                message = message
            ) { status, log ->
                if (status == "SENT" || status == "SEND_FAILED" || status == "CANCELLED") {
                    completedExecutions.add(executionId)
                }
                taskStateMap[taskId] = status
            }
        }
    }

    @Synchronized
    fun claimTaskForSending(context: Context, taskId: String): Boolean {
        val currentState = taskStateMap[taskId] ?: "PENDING"
        if (currentState == "SENDING" || currentState == "SENT") {
            Log.w(TAG, "Task $taskId state is already $currentState. Atomic claim denied.")
            return false
        }
        taskStateMap[taskId] = "SENDING"
        removePendingTask(context, taskId)
        return true
    }

    fun registerPendingTaskForUnlock(
        context: Context,
        taskId: String,
        executionId: String,
        recipient: String,
        message: String
    ) {
        try {
            taskStateMap[taskId] = "WAITING_FOR_UNLOCK"
            val prefs = context.getSharedPreferences(PREFS_PENDING, Context.MODE_PRIVATE)
            val jsonStr = prefs.getString(KEY_PENDING_TASKS, "[]") ?: "[]"
            val array = JSONArray(jsonStr)

            val filtered = JSONArray()
            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                if (obj.optString("taskId") != taskId) {
                    filtered.put(obj)
                }
            }

            val newObj = JSONObject().apply {
                put("taskId", taskId)
                put("executionId", executionId)
                put("recipient", recipient)
                put("message", message)
                put("registeredAt", System.currentTimeMillis())
            }
            filtered.put(newObj)

            prefs.edit().putString(KEY_PENDING_TASKS, filtered.toString()).apply()
            Log.i(TAG, "Registered pending task for unlock: taskId=$taskId to $recipient")

            postPendingUnlockNotification(context, recipient)
        } catch (e: Exception) {
            Log.e(TAG, "Error registering pending task for unlock: ${e.message}", e)
        }
    }

    private fun removePendingTask(context: Context, taskId: String) {
        try {
            val prefs = context.getSharedPreferences(PREFS_PENDING, Context.MODE_PRIVATE)
            val jsonStr = prefs.getString(KEY_PENDING_TASKS, "[]") ?: "[]"
            val array = JSONArray(jsonStr)
            val filtered = JSONArray()
            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                if (obj.optString("taskId") != taskId) {
                    filtered.put(obj)
                }
            }
            prefs.edit().putString(KEY_PENDING_TASKS, filtered.toString()).apply()
        } catch (e: Exception) {
            Log.e(TAG, "Error removing pending task: ${e.message}")
        }
    }

    fun hasPendingUnlockTasks(context: Context): Boolean {
        return try {
            val prefs = context.getSharedPreferences(PREFS_PENDING, Context.MODE_PRIVATE)
            val jsonStr = prefs.getString(KEY_PENDING_TASKS, "[]") ?: "[]"
            val array = JSONArray(jsonStr)
            array.length() > 0
        } catch (_: Exception) {
            false
        }
    }

    fun onDeviceUnlocked(context: Context) {
        Log.i(TAG, "Legitimate USER_PRESENT unlock detected. Checking pending tasks...")
        try {
            val prefs = context.getSharedPreferences(PREFS_PENDING, Context.MODE_PRIVATE)
            val jsonStr = prefs.getString(KEY_PENDING_TASKS, "[]") ?: "[]"
            val array = JSONArray(jsonStr)

            if (array.length() == 0) {
                Log.i(TAG, "No pending tasks waiting for unlock.")
                return
            }

            Log.i(TAG, "Found ${array.length()} pending task(s) waiting for unlock. Processing...")

            // Clear pending list BEFORE execution to prevent duplicate triggers
            prefs.edit().remove(KEY_PENDING_TASKS).apply()

            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                val taskId = obj.optString("taskId")
                val executionId = obj.optString("executionId")
                val recipient = obj.optString("recipient")
                val message = obj.optString("message")

                if (completedExecutions.contains(executionId)) {
                    Log.w(TAG, "Task $taskId (executionId=$executionId) already executed. Skipping.")
                    continue
                }

                Log.i(TAG, "Automatically resuming pending task $taskId for $recipient...")

                NexaAutomationEngine.executeUnlockedTask(
                    context = context,
                    taskId = taskId,
                    executionId = executionId,
                    recipient = recipient,
                    message = message
                ) { status, log ->
                    if (status == "SENT" || status == "SEND_FAILED" || status == "CANCELLED") {
                        completedExecutions.add(executionId)
                    }
                    taskStateMap[taskId] = status

                    broadcastTaskState(
                        taskId = taskId,
                        executionId = executionId,
                        status = status,
                        recipient = recipient,
                        message = message,
                        log = log
                    )
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error processing pending tasks on unlock: ${e.message}", e)
        }
    }

    private fun postPendingUnlockNotification(context: Context, recipient: String) {
        try {
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            val channelId = "nexa_pending_unlock_channel"

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val channel = NotificationChannel(
                    channelId,
                    "NEXA Pending Tasks",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Notifications for scheduled tasks waiting for device unlock"
                    lockscreenVisibility = Notification.VISIBILITY_PUBLIC
                }
                notificationManager.createNotificationChannel(channel)
            }

            val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Notification.Builder(context, channelId)
            } else {
                @Suppress("DEPRECATION")
                Notification.Builder(context)
            }

            val notification = builder
                .setContentTitle("NEXA Scheduler: Message Pending 🔒")
                .setContentText("Scheduled message will send automatically when you unlock.")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setPriority(Notification.PRIORITY_HIGH)
                .setAutoCancel(true)
                .build()

            notificationManager.notify(8888, notification)
        } catch (e: Exception) {
            Log.e(TAG, "Error posting pending unlock notification: ${e.message}")
        }
    }

    fun restoreScheduledTasksAfterBoot(context: Context) {
        Log.i(TAG, "Restoring scheduled tasks after boot complete.")
        try {
            val prefs = context.getSharedPreferences(PREFS_PENDING, Context.MODE_PRIVATE)
            val jsonStr = prefs.getString(KEY_PENDING_TASKS, "[]") ?: "[]"
            val array = JSONArray(jsonStr)

            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                val taskId = obj.optString("taskId")
                Log.d(LOG_TAG, "taskId=$taskId stage=TASK_REARMED_AFTER_BOOT")
            }

            if (array.length() > 0) {
                NexaForegroundService.startService(context)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in restoreScheduledTasksAfterBoot: ${e.message}")
        }
    }

    private fun broadcastTaskState(
        taskId: String,
        executionId: String,
        status: String,
        recipient: String,
        message: String,
        log: String
    ) {
        val data = mapOf(
            "taskId" to taskId,
            "executionId" to executionId,
            "status" to status,
            "recipient" to recipient,
            "message" to message,
            "log" to log,
            "timestamp" to System.currentTimeMillis()
        )
        android.os.Handler(android.os.Looper.getMainLooper()).post {
            try {
                automationEventSink?.success(data)
            } catch (e: Exception) {
                Log.e(TAG, "Error posting event to Flutter sink: ${e.message}")
            }
        }
    }
}
