package com.nexa.nexa_app

import android.app.KeyguardManager
import android.content.Context
import android.content.Intent
import android.database.Cursor
import android.net.Uri
import android.provider.ContactsContract
import android.util.Log

object WhatsAppTaskManager {
    private const val TAG = "WhatsAppTaskManager"
    private const val LOG_TAG = "NEXA_SCHED"

    fun executeTask(
        context: Context,
        taskId: String,
        executionId: String,
        recipient: String,
        message: String,
        broadcastState: (status: String, log: String) -> Unit
    ) {
        val kgm = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        val isLocked = kgm?.isKeyguardLocked ?: false

        Log.i(TAG, "WhatsAppTaskManager Stage 2 starting for $taskId -> $recipient (Device Locked: $isLocked)")

        // 1. Check Package Availability -> WHATSAPP_READY
        val pm = context.packageManager
        var installedPackage: String? = null
        try {
            pm.getPackageInfo("com.whatsapp", 0)
            installedPackage = "com.whatsapp"
        } catch (_: Exception) {
            try {
                pm.getPackageInfo("com.whatsapp.w4b", 0)
                installedPackage = "com.whatsapp.w4b"
            } catch (_: Exception) {}
        }

        if (installedPackage == null) {
            Log.e(TAG, "WhatsApp is not installed on this device.")
            Log.d(LOG_TAG, "taskId=$taskId stage=TASK_FAILED reason=whatsapp_not_installed")
            broadcastState("WHATSAPP_UNAVAILABLE", "WhatsApp application is not installed on device.")
            return
        }

        broadcastState("WHATSAPP_READY", "WhatsApp package ($installedPackage) verified & ready.")

        // 2. Resolve Contact Name / Phone Number -> RECIPIENT_SELECTED & MESSAGE_ENTERED
        val resolvedPhone = resolvePhoneNumber(context, recipient)
        Log.d(LOG_TAG, "taskId=$taskId stage=RECIPIENT_SELECTED")
        Log.d(LOG_TAG, "taskId=$taskId stage=MESSAGE_ENTERED")
        broadcastState("COMPOSING", "Composing message for $recipient...")

        try {
            val intentUrl = if (resolvedPhone.length >= 7) {
                "https://api.whatsapp.com/send?phone=$resolvedPhone&text=${Uri.encode(message)}"
            } else {
                // Contact name could not be converted to raw digits; set for Accessibility contact search
                NexoGestureUnlockService.activePendingContactName = recipient
                "https://api.whatsapp.com/send?text=${Uri.encode(message)}"
            }

            val waIntent = Intent(Intent.ACTION_VIEW, Uri.parse(intentUrl)).apply {
                setPackage(installedPackage)
                addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK or
                    Intent.FLAG_ACTIVITY_CLEAR_TOP or
                    Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED
                )
            }

            // 3. Dispatch Intent -> OPEN_WHATSAPP & SEND_TAPPED
            Log.d(LOG_TAG, "taskId=$taskId stage=OPEN_WHATSAPP")
            Log.d(LOG_TAG, "taskId=$taskId stage=SEND_TAPPED")
            broadcastState("SENDING", "Opening WhatsApp chat and tapping send...")
            context.startActivity(waIntent)

            // 4. Verification -> VERIFYING (Delayed 3.5s to allow Accessibility auto-click)
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                broadcastState("VERIFYING", "Verifying message submission in WhatsApp...")

                NexaTaskVerificationManager.verifyTaskSubmission(
                    taskId = taskId,
                    executionId = executionId,
                    recipient = recipient,
                    message = message
                ) { isSent, details ->
                    val clicked = NexoGestureUnlockService.wasSendButtonClickedRecently(4000)
                    if (isSent || clicked) {
                        Log.d(LOG_TAG, "taskId=$taskId stage=SEND_VERIFIED")
                        Log.d(LOG_TAG, "taskId=$taskId stage=TASK_SENT")
                        broadcastState("SENT", "Scheduled message sent successfully. You can restore your Pattern/PIN lock now.")
                    } else {
                        Log.d(LOG_TAG, "taskId=$taskId stage=SEND_VERIFICATION_FAILED")
                        Log.d(LOG_TAG, "taskId=$taskId stage=TASK_FAILED reason=send_button_not_clicked")
                        broadcastState("VERIFICATION_FAILED", "Send button was not clicked in WhatsApp.")
                    }
                }
            }, 3500)
        } catch (e: Exception) {
            Log.e(TAG, "Error in WhatsAppTaskManager: ${e.message}", e)
            Log.d(LOG_TAG, "taskId=$taskId stage=TASK_FAILED reason=${e.message}")
            broadcastState("SEND_FAILED", "Send failed: ${e.message}")
        }
    }

    private fun resolvePhoneNumber(context: Context, recipient: String): String {
        val digitsOnly = recipient.replace("[^0-9]".toRegex(), "")
        if (digitsOnly.length >= 7) {
            return digitsOnly
        }

        try {
            val cursor: Cursor? = context.contentResolver.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                arrayOf(ContactsContract.CommonDataKinds.Phone.NUMBER),
                "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?",
                arrayOf("%$recipient%"),
                null
            )
            cursor?.use { c ->
                if (c.moveToFirst()) {
                    val numIdx = c.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER)
                    if (numIdx != -1) {
                        val rawNumber = c.getString(numIdx)
                        val phone = rawNumber.replace("[^0-9]".toRegex(), "")
                        if (phone.length >= 7) {
                            Log.i(TAG, "Resolved contact name '$recipient' to device phone number: $phone")
                            return phone
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error querying device contacts for '$recipient': ${e.message}")
        }

        return digitsOnly
    }
}
