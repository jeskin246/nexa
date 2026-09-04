package com.nexa.nexa_app

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log

object NexaSchedulerManager {
    private const val TAG = "NexaSchedulerManager"

    fun scheduleTaskAlarm(
        context: Context,
        taskId: String,
        executionId: String,
        recipient: String,
        message: String,
        timestamp: Long
    ): Boolean {
        try {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val intent = Intent(context, NexaAlarmReceiver::class.java).apply {
                putExtra("taskId", taskId)
                putExtra("executionId", executionId)
                putExtra("recipient", recipient)
                putExtra("message", message)
            }

            val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }

            val pendingIntent = PendingIntent.getBroadcast(
                context,
                taskId.hashCode(),
                intent,
                flags
            )

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, timestamp, pendingIntent)
            } else {
                alarmManager.setExact(AlarmManager.RTC_WAKEUP, timestamp, pendingIntent)
            }

            val delayMs = timestamp - System.currentTimeMillis()
            Log.i(TAG, "NexaSchedulerManager scheduled exact alarm for $taskId to $recipient in ${delayMs / 1000}s")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "NexaSchedulerManager error: ${e.message}", e)
            return false
        }
    }

    fun cancelTaskAlarm(context: Context, taskId: String) {
        try {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val intent = Intent(context, NexaAlarmReceiver::class.java)
            val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }
            val pendingIntent = PendingIntent.getBroadcast(context, taskId.hashCode(), intent, flags)
            alarmManager.cancel(pendingIntent)
            Log.i(TAG, "NexaSchedulerManager cancelled alarm for $taskId")
        } catch (e: Exception) {
            Log.e(TAG, "NexaSchedulerManager cancel error: ${e.message}", e)
        }
    }
}
