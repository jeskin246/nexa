package com.nexa.nexa_app

import android.app.Activity
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.util.Log
import android.view.WindowManager

class NexaTaskExecutionActivity : Activity() {

    companion object {
        private const val TAG = "NexaTaskExecActivity"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Allow Activity to display over keyguard & turn display screen ON
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
            val kgm = getSystemService(Context.KEYGUARD_SERVICE) as? android.app.KeyguardManager
            kgm?.requestDismissKeyguard(this, null)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
                WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD or
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            )
        }

        val pm = getSystemService(Context.POWER_SERVICE) as? PowerManager
        @Suppress("DEPRECATION")
        val wakeLock = pm?.newWakeLock(
            PowerManager.FULL_WAKE_LOCK or
            PowerManager.ACQUIRE_CAUSES_WAKEUP or
            PowerManager.ON_AFTER_RELEASE,
            "NexaOS:TaskWakeUp"
        )
        wakeLock?.acquire(6000)

        val taskId = intent.getStringExtra("taskId") ?: ""
        val executionId = intent.getStringExtra("executionId") ?: ""
        val recipient = intent.getStringExtra("recipient") ?: ""
        val message = intent.getStringExtra("message") ?: ""

        Log.i(TAG, "NexaTaskExecutionActivity displayed over lockscreen for taskId=$taskId recipient=$recipient")

        // Trigger task sequence via NexaAutomationEngine over Keyguard Activity
        NexaAutomationEngine.processScheduledTask(
            context = applicationContext,
            taskId = taskId,
            executionId = executionId,
            recipient = recipient,
            message = message
        ) { status, log ->
            Log.d(TAG, "Task state callback: status=$status log=$log")
        }

        // Finish activity after 1.2 seconds so WhatsApp window is brought front-and-center
        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
            if (!isFinishing) {
                finish()
            }
        }, 1200L)
    }
}
