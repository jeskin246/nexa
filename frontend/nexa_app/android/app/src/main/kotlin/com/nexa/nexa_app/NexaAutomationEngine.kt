package com.nexa.nexa_app

import android.app.KeyguardManager
import android.content.Context
import android.os.PowerManager
import android.util.Log

object NexaAutomationEngine {
    private const val TAG = "NexaAutomationEngine"
    private const val LOG_TAG = "NEXA_SCHED"

    fun processScheduledTask(
        context: Context,
        taskId: String,
        executionId: String,
        recipient: String,
        message: String,
        broadcastState: (status: String, log: String) -> Unit
    ) {
        Log.d(LOG_TAG, "taskId=$taskId stage=CHECKING_DEVICE")

        val kgm = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        val pm = context.getSystemService(Context.POWER_SERVICE) as? PowerManager

        val isLocked = kgm?.isKeyguardLocked ?: false
        val isInteractive = pm?.isInteractive ?: true

        Log.i(TAG, "Device state check: KeyguardLocked=$isLocked Interactive=$isInteractive")

        // 1. ALWAYS Wake display screen ON
        wakeScreenIfOff(context)

        val handler = android.os.Handler(android.os.Looper.getMainLooper())

        // 2. Perform Swipe UP gesture to swipe away lockscreen clock
        handler.postDelayed({
            if (NexoGestureUnlockService.isServiceRunning()) {
                Log.d(LOG_TAG, "taskId=$taskId stage=SWIPE_UNLOCK_START")
                broadcastState("SYSTEM_AUTHENTICATION", "Swiping screen to dismiss lockscreen...")
                NexoGestureUnlockService.instance?.performAutomatedUnlock("SWIPE", "")
            }

            // 3. Launch WhatsApp intent to open contact, type message, and send
            handler.postDelayed({
                if (NexaTaskService.claimTaskForSending(context, taskId)) {
                    Log.d(LOG_TAG, "taskId=$taskId stage=SENDING_START")
                    broadcastState("SENDING", "Opening WhatsApp to send message...")
                    WhatsAppTaskManager.executeTask(context, taskId, executionId, recipient, message, broadcastState)
                }
            }, 700L)
        }, 400L)
    }

    fun executeUnlockedTask(
        context: Context,
        taskId: String,
        executionId: String,
        recipient: String,
        message: String,
        broadcastState: (status: String, log: String) -> Unit
    ) {
        Log.d(LOG_TAG, "taskId=$taskId stage=TASK_CLAIMED")

        if (NexaTaskService.claimTaskForSending(context, taskId)) {
            Log.d(LOG_TAG, "taskId=$taskId stage=SENDING_START")
            broadcastState("SENDING", "Automatically resuming pending task after unlock...")

            wakeScreenIfOff(context)
            WhatsAppTaskManager.executeTask(context, taskId, executionId, recipient, message, broadcastState)
        } else {
            Log.w(TAG, "Task $taskId already claimed or sent. Skipping duplicate send.")
        }
    }

    private fun wakeScreenIfOff(context: Context) {
        try {
            val pm = context.getSystemService(Context.POWER_SERVICE) as? PowerManager
            if (pm != null && !pm.isInteractive) {
                @Suppress("DEPRECATION")
                val screenLock = pm.newWakeLock(
                    PowerManager.FULL_WAKE_LOCK or
                    PowerManager.ACQUIRE_CAUSES_WAKEUP or
                    PowerManager.ON_AFTER_RELEASE,
                    "NexaOS:ScreenWakeUpLock"
                )
                screenLock.acquire(5000)
                Log.i(TAG, "Acquired Screen WakeLock")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in wakeScreenIfOff: ${e.message}")
        }
    }
}
