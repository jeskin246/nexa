package com.nexa.nexa_app

import android.app.Notification
import android.app.RemoteInput
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import io.flutter.plugin.common.EventChannel

class NexoNotificationListener : NotificationListenerService() {

    companion object {
        private const val TAG = "NexoNotifListener"

        // Map to store direct reply action references keyed by unique notification key
        val replyActionMap = HashMap<String, Pair<Notification.Action, RemoteInput>>()

        var eventSink: EventChannel.EventSink? = null

        fun sendDirectReply(context: Context, key: String, replyText: String): Boolean {
            try {
                val pair = replyActionMap[key]
                if (pair == null) {
                    Log.e(TAG, "No direct reply action found for key: $key. Current stored keys count: ${replyActionMap.size}")
                    return false
                }

                val action = pair.first
                val remoteInput = pair.second

                val intent = Intent()
                val bundle = Bundle()
                bundle.putCharSequence(remoteInput.resultKey, replyText)
                RemoteInput.addResultsToIntent(arrayOf(remoteInput), intent, bundle)

                action.actionIntent.send(context.applicationContext, 0, intent)
                Log.i(TAG, "Direct reply sent successfully for key: $key")
                return true
            } catch (e: Exception) {
                Log.e(TAG, "Error sending direct reply: ${e.message}", e)
                return false
            }
        }
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        try {
            val packageName = sbn.packageName ?: return

            // Filter supported apps: WhatsApp (including Business), Instagram, Telegram
            val appName = when (packageName) {
                "com.whatsapp", "com.whatsapp.w4b" -> "WhatsApp"
                "com.instagram.android" -> "Instagram"
                "org.telegram.messenger", "org.telegram.messenger.web" -> "Telegram"
                else -> return
            }

            val extras = sbn.notification?.extras ?: return
            var title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
            var text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""

            if (title.isEmpty()) {
                title = extras.getCharSequence(Notification.EXTRA_TITLE_BIG)?.toString() ?: "Message"
            }
            if (text.isEmpty()) {
                text = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString() ?: ""
            }

            // Skip ongoing notifications
            if ((sbn.notification.flags and Notification.FLAG_ONGOING_EVENT) != 0) return

            // Inspect notification actions for RemoteInput direct reply
            var foundAction: Notification.Action? = null
            var foundRemoteInput: RemoteInput? = null

            val actions = sbn.notification.actions
            if (actions != null) {
                for (action in actions) {
                    val remoteInputs = action.remoteInputs
                    if (remoteInputs != null && remoteInputs.isNotEmpty()) {
                        for (ri in remoteInputs) {
                            if (ri.resultKey != null) {
                                foundAction = action
                                foundRemoteInput = ri
                                break
                            }
                        }
                    }
                    if (foundAction != null) break
                }
            }

            val notificationKey = "${packageName}_${sbn.id}_${System.currentTimeMillis()}"

            val hasDirectReply = foundAction != null && foundRemoteInput != null
            if (hasDirectReply && foundAction != null && foundRemoteInput != null) {
                replyActionMap[notificationKey] = Pair(foundAction, foundRemoteInput)
            }

            Log.i(TAG, "Notification detected from $appName ($title): hasDirectReply=$hasDirectReply key=$notificationKey")

            val eventData = mapOf(
                "notificationKey" to notificationKey,
                "appName" to appName,
                "packageName" to packageName,
                "sender" to title,
                "message" to text,
                "hasDirectReply" to hasDirectReply,
                "timestamp" to System.currentTimeMillis()
            )

            // Broadcast to Flutter event sink on UI main looper thread
            android.os.Handler(android.os.Looper.getMainLooper()).post {
                try {
                    eventSink?.success(eventData)
                } catch (e: Exception) {
                    Log.e(TAG, "Error posting notification event to Flutter sink: ${e.message}")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in onNotificationPosted: ${e.message}", e)
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        super.onNotificationRemoved(sbn)
    }
}
