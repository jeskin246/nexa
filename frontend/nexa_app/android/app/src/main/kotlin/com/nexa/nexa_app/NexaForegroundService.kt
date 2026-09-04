package com.nexa.nexa_app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.IBinder
import android.util.Log

class NexaForegroundService : Service() {

    companion object {
        private const val TAG = "NexaForegroundService"
        private const val LOG_TAG = "NEXA_SCHED"
        private const val CHANNEL_ID = "nexa_foreground_service_channel"
        private const val NOTIFICATION_ID = 1001

        fun startService(context: Context) {
            try {
                val intent = Intent(context, NexaForegroundService::class.java)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(intent)
                } else {
                    context.startService(intent)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error starting NexaForegroundService: ${e.message}", e)
            }
        }

        fun stopService(context: Context) {
            try {
                val intent = Intent(context, NexaForegroundService::class.java)
                context.stopService(intent)
            } catch (e: Exception) {
                Log.e(TAG, "Error stopping NexaForegroundService: ${e.message}", e)
            }
        }
    }

    private var userPresentReceiver: BroadcastReceiver? = null

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "NexaForegroundService created")
        createNotificationChannel()

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    createNotification(),
                    android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
                )
            } else {
                startForeground(NOTIFICATION_ID, createNotification())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in startForeground: ${e.message}", e)
            try {
                startForeground(NOTIFICATION_ID, createNotification())
            } catch (e2: Exception) {
                Log.e(TAG, "Fallback startForeground exception: ${e2.message}")
            }
        }

        registerUserPresentReceiver()
    }

    private fun registerUserPresentReceiver() {
        if (userPresentReceiver != null) return

        userPresentReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (intent == null || context == null) return
                if (intent.action == Intent.ACTION_USER_PRESENT) {
                    Log.d(LOG_TAG, "stage=USER_PRESENT_RECEIVED")
                    Log.i(TAG, "ACTION_USER_PRESENT received. Triggering unlock task processor...")
                    
                    NexaTaskService.onDeviceUnlocked(context)

                    // If all WAITING_FOR_UNLOCK tasks are drained, stop foreground service
                    if (!NexaTaskService.hasPendingUnlockTasks(context)) {
                        Log.i(TAG, "All WAITING_FOR_UNLOCK tasks drained. Stopping NexaForegroundService.")
                        stopSelf()
                    }
                }
            }
        }

        val filter = IntentFilter(Intent.ACTION_USER_PRESENT)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(userPresentReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(userPresentReceiver, filter)
        }
        Log.i(TAG, "Dynamically registered USER_PRESENT BroadcastReceiver inside NexaForegroundService")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "NexaForegroundService onStartCommand - Active for WAITING_FOR_UNLOCK tasks")
        registerUserPresentReceiver()
        return START_STICKY
    }

    override fun onDestroy() {
        if (userPresentReceiver != null) {
            try {
                unregisterReceiver(userPresentReceiver)
                userPresentReceiver = null
                Log.i(TAG, "Unregistered USER_PRESENT BroadcastReceiver")
            } catch (e: Exception) {
                Log.e(TAG, "Error unregistering USER_PRESENT receiver: ${e.message}")
            }
        }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "NEXA OS Background Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps NEXA OS Automation active to process scheduled messages upon unlock"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }

        return builder
            .setContentTitle("NEXA OS Background Service")
            .setContentText("1 or more messages queued — will send automatically after unlock")
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setOngoing(true)
            .build()
    }
}
