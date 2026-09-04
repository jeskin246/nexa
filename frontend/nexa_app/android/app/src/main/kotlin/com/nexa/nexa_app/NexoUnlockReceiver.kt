package com.nexa.nexa_app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.util.Log

class NexoUnlockReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "NexoUnlockReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (Intent.ACTION_USER_PRESENT == intent.action) {
            Log.d(TAG, "ACTION_USER_PRESENT received: User unlocked device!")

            val mainHandler = Handler(Looper.getMainLooper())
            mainHandler.post {
                ScheduledWhatsAppPlugin.methodChannel?.invokeMethod("onUserUnlockedDevice", mapOf<String, Any>())
                Log.d(TAG, "Sent onUserUnlockedDevice event to Flutter engine")
            }
        }
    }
}
