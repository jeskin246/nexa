package com.nexa.nexa_app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.PowerManager
import android.util.Log

class NexaAlarmReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "NexaAlarmReceiver"
        private const val LOG_TAG = "NEXA_SCHED"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val taskId = intent.getStringExtra("taskId") ?: return
        val executionId = intent.getStringExtra("executionId") ?: ""
        val recipient = intent.getStringExtra("recipient") ?: ""
        val message = intent.getStringExtra("message") ?: ""

        Log.d(LOG_TAG, "taskId=$taskId stage=TRIGGER_FIRED")
        Log.i(TAG, "Scheduled Alarm Triggered for taskId=$taskId (executionId=$executionId)")

        // Acquire temporary Screen WakeLock to handle Doze Mode / Screen OFF
        val pm = context.getSystemService(Context.POWER_SERVICE) as? PowerManager
        @Suppress("DEPRECATION")
        val wakeLock = pm?.newWakeLock(
            PowerManager.FULL_WAKE_LOCK or
            PowerManager.ACQUIRE_CAUSES_WAKEUP or
            PowerManager.ON_AFTER_RELEASE,
            "NexaOS:AlarmWakeLock"
        )
        wakeLock?.acquire(10000)

        try {
            NexaTaskService.processAlarmTrigger(
                context = context,
                taskId = taskId,
                executionId = executionId,
                recipient = recipient,
                message = message
            )
        } finally {
            if (wakeLock?.isHeld == true) {
                wakeLock.release()
            }
        }
    }
}
