package com.nexa.nexa_app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.PowerManager
import android.util.Log

class NexoScheduledMessageReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "NexoScheduledReceiver"
        private const val LOG_TAG = "NEXA_SCHED"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val jobId = intent.getStringExtra("jobId") ?: "job_${System.currentTimeMillis()}"
        val contact = intent.getStringExtra("contact") ?: intent.getStringExtra("recipient") ?: "Unknown"
        val message = intent.getStringExtra("message") ?: ""

        Log.d(LOG_TAG, "taskId=$jobId stage=TRIGGER_FIRED")
        Log.i(TAG, "Scheduled alarm triggered for jobId=$jobId to $contact")

        // Acquire temporary Screen WakeLock
        val pm = context.getSystemService(Context.POWER_SERVICE) as? PowerManager
        @Suppress("DEPRECATION")
        val wakeLock = pm?.newWakeLock(
            PowerManager.FULL_WAKE_LOCK or
            PowerManager.ACQUIRE_CAUSES_WAKEUP or
            PowerManager.ON_AFTER_RELEASE,
            "Nexo:AlarmWakeLock"
        )
        wakeLock?.acquire(10000)

        try {
            NexaTaskService.processAlarmTrigger(
                context = context,
                taskId = jobId,
                executionId = jobId,
                recipient = contact,
                message = message
            )
        } finally {
            if (wakeLock?.isHeld == true) {
                wakeLock.release()
            }
        }
    }
}
